import streamlit as st
from gradio_client import Client, file
import tempfile
from PIL import Image
import requests
from io import BytesIO

client = Client("Nymbo/Virtual-Try-On", 120.0)

st.title("Virtual Try-On")

# Upload model image
background_image = st.file_uploader("Upload Model Image", type=["png", "jpg", "jpeg"])

# Predefined garment examples
garment_examples = [
    ("https://nymbo-virtual-try-on.hf.space/file=/tmp/gradio/c6a00bd87f53c541a88f163290a869d3fea67bd8/09133_00.jpg", "White Pretty Dress"),
    ("https://i.imgur.com/0DKjAml.jpeg", "Blue T-Shirt")
]

# Display predefined outfit images
st.subheader("Choose an outfit:")
selected_garment = None

if 'selected_garment' not in st.session_state:
    st.session_state.selected_garment = None

cols = st.columns(len(garment_examples))
for idx, (url, desc) in enumerate(garment_examples):
    with cols[idx]:
        if st.button(desc):
            st.session_state.selected_garment = (url, desc)
        st.image(url, caption=desc, use_column_width=True)

# Debug statement to see the selected garment
st.write("Selected garment:", st.session_state.selected_garment)

# Upload custom garment image
st.subheader("Or upload your own outfit image:")
garment_image = st.file_uploader("Upload Outfit Image", type=["png", "jpg", "jpeg"])
garment_description = st.text_input("Enter Outfit Description") if garment_image else ""

# Button to submit
if st.button("Try On"):
    if background_image is not None and (garment_image or st.session_state.selected_garment):
        with st.spinner("Processing..."):
            try:
                # Save the uploaded model image to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as bg_temp:
                    bg_temp.write(background_image.getbuffer())
                    bg_temp_path = bg_temp.name

                # Determine the garment image and description
                if garment_image:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as garm_temp:
                        garm_temp.write(garment_image.getbuffer())
                        garm_temp_path = garm_temp.name
                    garment_description = garment_description
                else:
                    garment_url, garment_description = st.session_state.selected_garment
                    response = requests.get(garment_url)
                    garm_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    garm_temp.write(response.content)
                    garm_temp_path = garm_temp.name
                    garm_temp.close()

                # Prepare input data for the API call
                input_dict = {
                    "background": file(bg_temp_path),
                    "layers": [],
                    "composite": None
                }

                # Call the API
                result = client.predict(
                    dict=input_dict,
                    garm_img=file(garm_temp_path),
                    garment_des=garment_description,
                    is_checked=True,
                    is_checked_crop=False,
                    denoise_steps=30,
                    seed=42,
                    api_name="/tryon"
                )

                # Display results
                st.image(result[0], caption="Output Image")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.error("Please upload a model image and choose or upload an outfit image.")
