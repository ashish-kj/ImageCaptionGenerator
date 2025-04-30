import streamlit as st
import requests
from PIL import Image
import io

st.set_page_config(page_title="Image Caption Generator (LLaVA)", layout="centered")

st.title("📷 Image Caption Generator")
st.caption("Using LLaVA via Ollama")

# Define the backend API endpoint
BACKEND_URL = "http://localhost:8000/caption/"

uploaded_file = st.file_uploader(
    "Choose an image...",
    type=["png", "jpg", "jpeg"],
    help="Upload an image file to generate a caption."
)

if uploaded_file is not None:
    # Display the uploaded image
    try:
        image = Image.open(uploaded_file)
        # Convert image to RGB to prevent potential errors with RGBA or other formats
        if image.mode != 'RGB':
            image = image.convert('RGB')

        st.image(image, caption="Uploaded Image", use_container_width=True)

        # Button to trigger caption generation
        if st.button("✨ Generate Caption", type="primary"):
            with st.spinner("Generating caption... Please wait."):
                # Prepare the file for the backend request
                # Rewind the file pointer just in case it was read before
                uploaded_file.seek(0)
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                try:
                    # Send request to the backend
                    res = requests.post(BACKEND_URL, files=files, timeout=90) # Increased timeout for potentially slow models

                    if res.status_code == 200:
                        result = res.json()
                        caption = result.get("caption")

                        if caption:
                            st.subheader("Generated Caption:")
                            st.write(f"**{caption}**")
                        else:
                            st.warning("⚠️ Backend returned an empty caption.")
                    else:
                        # Try to get error detail from backend response
                        try:
                            error_detail = res.json().get("detail", res.text)
                        except requests.exceptions.JSONDecodeError:
                            error_detail = res.text
                        st.error(f"❌ Error from backend (HTTP {res.status_code}): {error_detail}")


                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Connection Error: Could not connect to the backend at {BACKEND_URL}. Is it running?")
                except requests.exceptions.Timeout:
                     st.error(f"⏰ Timeout: The request to the backend timed out after 90 seconds.")
                except requests.exceptions.RequestException as e:
                    st.error(f"🚫 Request Error: Could not send request to backend. {e}")
                except Exception as e:
                    st.error(f"❓ An unexpected error occurred in the frontend: {e}")

    except Exception as e:
        st.error(f"🚨 Error loading or processing image: {e}")
else:
    st.info("Upload an image to get started.")


st.markdown("---")
st.markdown("Powered by [LLaVA](https://llava-vl.github.io/), [Ollama](https://ollama.com/), [FastAPI](https://fastapi.tiangolo.com/), and [Streamlit](https://streamlit.io/).") 