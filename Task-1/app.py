import streamlit as st
from diffusers import StableDiffusionPipeline
from PIL import Image
import torch
import os
import sqlite3
from datetime import datetime
import time

# Set page configuration
st.set_page_config(
    page_title="AI Image Generator by Ibrahim",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #000000;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .css-1d391kg {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .stExpander {
        border: 1px solid #333333;
        border-radius: 0.5rem;
        margin: 1rem 0;
        background-color: #1a1a1a;
    }
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    p, .stMarkdown {
        color: #e0e0e0;
    }
    .stTextInput > div > div > input {
        color: #ffffff;
        background-color: #1a1a1a;
    }
    .stTextArea > div > div > textarea {
        color: #ffffff;
        background-color: #1a1a1a;
    }
    .stSlider > div > div > div {
        color: #ffffff;
    }
    .stSelectbox > div > div > select {
        color: #ffffff;
        background-color: #1a1a1a;
    }
    .stExpander > div > div {
        color: #ffffff;
    }
    .stAlert {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .stSuccess {
        background-color: #1a1a1a;
        color: #4CAF50;
    }
    .stWarning {
        background-color: #1a1a1a;
        color: #ffa726;
    }
    .stError {
        background-color: #1a1a1a;
        color: #ef5350;
    }
    .stInfo {
        background-color: #1a1a1a;
        color: #29b6f6;
    }
    </style>
    """, unsafe_allow_html=True)

# Load the model only once
@st.cache_resource
def load_model():
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return pipe.to(device)

pipe = load_model()

# Connect to SQLite database
try:
    # Ensure images directory exists
    os.makedirs("images", exist_ok=True)
    
    conn = sqlite3.connect('prompts.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            image_path TEXT NOT NULL,
            expected_style TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            style_match_rating INTEGER,
            evaluation_notes TEXT
        )
    ''')
    conn.commit()
    print("Database connection successful")
except sqlite3.Error as e:
    print(f"Database error: {e}")
    st.error("Database connection failed")
except Exception as e:
    print(f"Error creating directories: {e}")
    st.error("Failed to create required directories")

# Sidebar
with st.sidebar:
    st.title("🎨 Ibrahim's Image Generator")
    st.markdown("---")
    st.markdown("### How to use")
    st.markdown("""
    1. Enter your prompt
    2. Specify the expected style
    3. Click Generate
    4. Rate the results
    """)
    st.markdown("---")
    st.markdown("### Tips")
    st.markdown("""
    - Be specific in your prompts
    - Try different styles
    - Provide feedback by rating the images
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.title("🖼️ Text-to-Image Generator")
    prompt = st.text_input("Enter your prompt", placeholder="A magical castle in the clouds...")
    expected_style = st.text_input("Enter expected style", placeholder="realistic, cartoon, cyberpunk...")

    if st.button("✨ Generate Image", use_container_width=True):
        if not prompt:
            st.warning("Please enter a prompt")
        else:
            # Create progress bar and text
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            try:
                # Simulate initial progress
                progress_bar.progress(25)
                progress_text.text("Preparing model... 25%")
                
                # Generate the image
                image = pipe(prompt).images[0]
                
                # Update progress
                progress_bar.progress(75)
                progress_text.text("Saving image... 75%")
                
                # Save the image
                os.makedirs("images", exist_ok=True)
                safe_prompt = prompt[:30].replace(' ', '_')
                safe_style = expected_style.replace(' ', '_') if expected_style else 'no_style'
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = f"images/{safe_prompt}_{safe_style}_{timestamp}.png"
                image.save(image_path)
                
                # Show 100% completion
                progress_bar.progress(100)
                progress_text.text("Generation complete! ✨")
                
                # Display the image
                st.image(image, caption=prompt, use_column_width=True)
                st.success(f"✨ Image saved successfully!")

                # Store in database
                try:
                    c.execute("""
                        INSERT INTO prompts (prompt, image_path, expected_style, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (prompt, image_path, expected_style, datetime.now()))
                    conn.commit()
                    print(f"Successfully inserted: Prompt: {prompt}, Path: {image_path}, Style: {expected_style}")
                except sqlite3.Error as e:
                    print(f"Database insertion error: {e}")
                    st.error("Failed to save to database")
            except Exception as e:
                print(f"Image generation error: {e}")
                st.error(f"Failed to generate image: {str(e)}")
            finally:
                # Clear progress indicators after 2 seconds
                time.sleep(2)
                progress_bar.empty()
                progress_text.empty()

# Search Section
st.markdown("---")
st.title("🔍 Search Gallery")
search_query = st.text_input("Search by prompt or style", key="search").lower()

# Gallery and Evaluation Section
st.markdown("---")
st.title("🖼️ Image Gallery")

try:
    print("Attempting to fetch gallery data...")
    if search_query:
        c.execute("""
            SELECT id, prompt, image_path, expected_style, created_at, style_match_rating, evaluation_notes
            FROM prompts 
            WHERE LOWER(prompt) LIKE ? OR LOWER(expected_style) LIKE ?
            ORDER BY created_at DESC
        """, (f'%{search_query}%', f'%{search_query}%'))
    else:
        c.execute("""
            SELECT id, prompt, image_path, expected_style, created_at, style_match_rating, evaluation_notes
            FROM prompts 
            ORDER BY created_at DESC
        """)
    
    rows = c.fetchall()
    print(f"Retrieved {len(rows)} rows from the database")
    
    if not rows:
        if search_query:
            st.info(f"🔍 No images found matching '{search_query}'")
        else:
            st.info("🎨 No images generated yet. Try creating your first masterpiece!")
    else:
        if search_query:
            st.success(f"🔍 Found {len(rows)} images matching '{search_query}'")
        
        # Create a grid layout for images
        cols = st.columns(3)
        for idx, row in enumerate(rows):
            with cols[idx % 3]:
                with st.expander(f"🎨 {row[1][:30]}...", expanded=False):
                    if os.path.exists(row[2]):
                        st.image(row[2], use_column_width=True)
                    else:
                        st.warning(f"Image file not found: {row[2]}")
                    st.write(f"**Prompt:** {row[1]}")
                    st.write(f"**Style:** {row[3]}")
                    st.write(f"**Created:** {row[4]}")
                    
                    st.markdown("---")
                    st.subheader("Style Match Evaluation")
                    rating = st.slider(
                        "How well does it match the style?",
                        min_value=1,
                        max_value=5,
                        value=row[5] if row[5] else 3,
                        key=f"rating_{row[0]}"
                    )
                    notes = st.text_area(
                        "Evaluation Notes",
                        value=row[6] if row[6] else "",
                        key=f"notes_{row[0]}"
                    )
                    
                    if st.button("💾 Save Evaluation", key=f"save_{row[0]}"):
                        try:
                            c.execute("""
                                UPDATE prompts 
                                SET style_match_rating = ?, evaluation_notes = ?
                                WHERE id = ?
                            """, (rating, notes, row[0]))
                            conn.commit()
                            st.success("✅ Evaluation saved!")
                        except sqlite3.Error as e:
                            print(f"Error saving evaluation: {e}")
                            st.error("❌ Failed to save evaluation")
except sqlite3.Error as e:
    print(f"Error retrieving gallery data: {e}")
    st.error(f"Failed to retrieve gallery data: {str(e)}")
except Exception as e:
    print(f"Unexpected error in gallery section: {e}")
    st.error(f"An unexpected error occurred: {str(e)}")

# Evaluation Summary
st.markdown("---")
st.title("📊 Style Performance Summary")

try:
    c.execute("""
        SELECT expected_style, 
               COUNT(*) as total_images,
               AVG(style_match_rating) as avg_rating
        FROM prompts
        WHERE style_match_rating IS NOT NULL
        GROUP BY expected_style
    """)
    summary_rows = c.fetchall()
    
    if summary_rows:
        cols = st.columns(len(summary_rows))
        for idx, (style, count, avg_rating) in enumerate(summary_rows):
            with cols[idx]:
                st.metric(
                    label=f"Style: {style}",
                    value=f"{avg_rating:.1f}/5",
                    delta=f"{count} images"
                )
                st.progress(avg_rating/5)
    else:
        st.info("📝 No evaluations available yet. Start rating your images!")
except sqlite3.Error as e:
    print(f"Error generating summary: {e}")
    st.error(f"Failed to generate summary: {str(e)}")

# Close the database connection at the end of the app
try:
    conn.close()
    print("Database connection closed")
except sqlite3.Error as e:
    print(f"Error closing database: {e}")
