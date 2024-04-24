import streamlit as st
import pandas as pd
import cv2
from streamlit_extras.tags import tagger_component
from streamlit_shortcuts import add_keyboard_shortcuts
import os

st.set_page_config(page_title="SWT OCR Annotator", layout="wide")

# -- SESSION STATE --

if "csv_file" not in st.session_state:
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="filepath")
    if uploaded_file is not None:
        if os.path.exists(uploaded_file.name):
            st.session_state["csv_file"] = uploaded_file.name
        else:
            st.session_state["csv_file"] = uploaded_file
        st.rerun()
    st.stop()

if "df" not in st.session_state:
    st.session_state["df"] = pd.read_csv(st.session_state["csv_file"])
    # Save the name as a string for server saving
    if not isinstance(st.session_state["csv_file"], str):
        st.session_state["csv_file"] = st.session_state["csv_file"].name
df = st.session_state["df"]

try:
    index = st.session_state.get("index", df.loc[df['annotated'] == False].index[0])
    st.session_state["index"] = index
except IndexError:
    st.header("All images annotated!")
    st.balloons()
    st.stop()

label_adjusted = st.session_state.get("label_adjusted", False)
st.session_state["label_adjusted"] = label_adjusted

ocr_rejected = st.session_state.get("ocr_rejected", False)
st.session_state["ocr_rejected"] = ocr_rejected

if "scene_label" not in st.session_state:
    st.session_state["scene_label"] = df["scene_label"].iloc[index]

# ----------------------

st.header(f"SWT OCR Annotator ({index}/{len(df)})", divider='gray')

sidebar = st.sidebar
with sidebar:
    continue_key = st.text_input("Continue Key", key="continue", value="Enter")
    reject_key = st.text_input("Reject Key", key="reject", value="x")
    swap_key = st.text_input("Swap Key", key="swap", value="s")
    delete_key = st.text_input("Delete Key", key="delete", value="Ctrl+Shift+X")
    st.divider()


# Shortcuts for key logging
keyboard_shortcuts = [f"**{continue_key}**: Continue", f"**{reject_key}**: Reject OCR (toggle)", f"**{swap_key}**: Swap frame type (toggle)", f"**{delete_key}**: Remove (invalid scene type)"]
tagger_component(
    "",
    keyboard_shortcuts,
    color_name=["rgb(38, 39, 48)", 'red', "blue", "orange"],
)
add_keyboard_shortcuts({
    continue_key: 'Continue',
    reject_key: 'Reject',
    swap_key: 'Swap',
    delete_key: 'Delete'
})

row = df.iloc[index]
fpath = row["path"]
timepoint = row["timePoint"]
scene_label = row["scene_label"]
formatted_text = row["textdocument"].replace("\n", "<br>")

# Get frame image from video
frame = cv2.VideoCapture(fpath)
frame.set(cv2.CAP_PROP_POS_MSEC, timepoint)
success, image = frame.read()

# Set styles for annotation panel
st.markdown("""
<style>
.big-font {
    font-size:25px !important;
}
.rejected {
    color: rgb(255, 75, 75);
}
</style>
""", unsafe_allow_html=True)

if success:
    col1, col2 = st.columns(2)
    with col1:
        # Image panel
        st.image(image, channels="BGR")
    with col2:
        with col2.container(border=True):
            # Scene label panel
            if label_adjusted:
                st.write(f"## :blue[{st.session_state['scene_label']}]")
            else:
                st.write(f"## {st.session_state['scene_label']} (confidence {row['confidence']:.2f})")
        with col2.container(border=True):
            # OCR text panel
            if ocr_rejected:
                st.markdown(f'<p class="big-font rejected">{formatted_text}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="big-font">{formatted_text}</p>', unsafe_allow_html=True)

else:
    st.write("Failed to retrieve frame from the specified timepoint.")

def continue_callback():
    global df
    df.loc[index, "ocr_accepted"] = not st.session_state["ocr_rejected"]
    next_example()

def reject_callback():
    ocr_rejected = not st.session_state["ocr_rejected"]
    st.session_state["ocr_rejected"] = ocr_rejected

def swap_callback():
    global df
    new_scene_label = "credits" if st.session_state["scene_label"] == "chyron" else "chyron"
    df.loc[index, "scene_label"] = new_scene_label
    df.loc[index, "label_adjusted"] = not st.session_state["label_adjusted"]
    st.session_state["scene_label"] = new_scene_label
    st.session_state["label_adjusted"] = not st.session_state["label_adjusted"]

def delete_callback():
    global df
    df.loc[index, "deleted"] = True
    next_example()

def next_example():
    global df, index
    df.loc[index, "annotated"] = True
    df.loc[index, "ocr_accepted"] = not st.session_state["ocr_rejected"]
    df.to_csv(st.session_state["csv_file"], index=False)
    st.session_state["index"] = index = index + 1
    refresh_all()

def refresh_all():
    global df, index
    df.loc[index, "deleted"] = False
    df.loc[index, "label_adjusted"] = False
    df.loc[index, "ocr_accepted"] = False
    st.session_state["ocr_rejected"] = False
    st.session_state["scene_label"] = df["scene_label"].iloc[st.session_state["index"]]
    st.session_state["label_adjusted"] = df.loc[st.session_state["index"], "label_adjusted"]

def undo():
    global df, index
    if index > 0:
        refresh_all()
        st.session_state["index"] = index = index - 1
        df.loc[st.session_state["index"], "annotated"] = False
        refresh_all()
        df.to_csv(st.session_state["csv_file"], index=False)

# Custom CSS to improve alignment issues
st.markdown("""
            <style>
                div[data-testid="column"] {
                    width: fit-content !important;
                    flex: unset;
                }
                div[data-testid="column"] * {
                    width: fit-content !important;
                }

            </style>
            """, unsafe_allow_html=True)


button_col1, button_col2, button_col3, button_col4 = st.columns(4)
with button_col1:
    st.button("Continue", on_click=continue_callback)
with button_col2:
    st.button("Reject", on_click=reject_callback)
with button_col3:
    st.button("Swap", on_click=swap_callback)
with button_col4:
    st.button("Delete", on_click=delete_callback)


with sidebar:
    st.button("Oops (Undo last annotation)", on_click=undo)

st.divider()

st.write(df)