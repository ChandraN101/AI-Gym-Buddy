import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from fuzzywuzzy import fuzz
import google.generativeai as gemini

# Step 1: Configure Gemini API Key
GEMINI_API_KEY = "AIzaSyCv55PrSEbS0GZVOH0MSWRrIUXpyytAB54"  # Replace with your actual API key
gemini.configure(api_key=GEMINI_API_KEY)

# Step 2: Load the dataset
df = pd.read_excel(r'C:\Users\CHANDRA N\OneDrive\Desktop\chandra n final mini project - Copy\chandra final mini project - Copy\gym-dataset.xlsx')

df.fillna('', inplace=True)  # Fill missing values with an empty string

# Helper function to process dataset values with multiple entries
def process_multiple_values(column):
    return column.apply(lambda x: ' '.join(x.split(', ')))

# Preprocess dataset columns with multiple values
df['BMI'] = process_multiple_values(df['BMI'])
df['Experience Level'] = process_multiple_values(df['Experience Level'])
df['Injury'] = process_multiple_values(df['Injury'])
df['Medication'] = process_multiple_values(df['Medication'])

# Step 3: Define a function to compute similarity
def get_similarity(user_input, dataset_column, weight_cosine=0.7, weight_fuzzy=0.3):
    vectorizer = TfidfVectorizer()
    all_data = dataset_column.tolist() + [user_input]
    tfidf_matrix = vectorizer.fit_transform(all_data)
    
    # Compute cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    
    # Compute fuzzy similarity
    fuzzy_sim = dataset_column.apply(lambda x: fuzz.partial_ratio(x, user_input) / 100.0)
    
    # Combine similarities
    combined_sim = weight_cosine * cosine_sim + weight_fuzzy * fuzzy_sim
    return combined_sim


def extract_10_exercises(response_text):
    start = response_text.find("10 Exercises") + len("10 Exercises")
    if start < len("10 Exercises"):  # If "10 Exercises" is not found
        return ""
    end = response_text.find("User Summary", start)
    if end == -1:  # If "User Summary" is not found, extract till the end
        end = len(response_text)
    return response_text[start:end].strip()


def extract_10_day_workout(response_text):
    start = response_text.find("10-Day Workout Routine") + len("10-Day Workout Routine")
    end = response_text.find("10 Exercises")
    return response_text[start:end].strip()


def extract_user_summary(response_text):
    start = response_text.find("User Summary") + len("User Summary")
    end = response_text.find("Diet Plan")
    return response_text[start:end].strip()


def clean_user_summary(user_summary):
    """
    Cleans the user summary by removing unnecessary formatting such as bold symbols (**)
    and leading colons or other unwanted characters.
    """
    cleaned_summary = user_summary.replace("**", "").strip()  # Remove bold markdown and strip whitespace
    return cleaned_summary.lstrip(":")  # Remove leading colon if present



def format_exercises_to_pointwise(text):
    import re

    # Remove unnecessary symbols like colons and asterisks
    text = text.replace(":", "").replace("**", "").strip()

    # Split by numbered items (e.g., "1.", "2.") but keep the numbered part separately
    exercise_lines = re.split(r'(\d+\.\s+)', text)  # Split on number with a period and space but keep numbers

    formatted_exercises = "<ol>"  # Start ordered list

    # Initialize a variable to accumulate exercise content
    exercise_content = ""

    # Loop through the split parts
    for part in exercise_lines:
        part = part.strip()  # Remove extra spaces
        if part and part[0].isdigit() and '.' in part:  # This part is a numbered item (e.g., "1. Squats")
            # If we already have some exercise content, close the current <li> tag and start a new one
            if exercise_content:
                formatted_exercises += f"<li>{exercise_content.strip()}</li><br>"  # Add a <br> for a gap
                exercise_content = ""  # Reset the exercise content

            # Skip the number and the period for this part, just add the exercise name/content
            exercise_content = part[part.index('.') + 1:].strip()  # Remove the number and period from the part

        elif part:  # This part is content for an exercise
            # Split by period to ensure the sentence ends at the first period
            sentences = part.split('. ')
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:  # Add non-empty sentences to the exercise content
                    exercise_content += sentence + ".<br>"  # Add a <br> after each sentence

    # Add the last accumulated exercise content
    if exercise_content:
        formatted_exercises += f"<li>{exercise_content.strip()}</li>"

    formatted_exercises += "</ol>"  # Close ordered list
    return formatted_exercises



def format_to_pointwise(text):
    import re

    # Remove unnecessary symbols (e.g., colons, asterisks, hyphens, etc.)
    text = re.sub(r'[:*\-]', '', text).strip()

    # Split text into items based on "Day X" headers
    items = re.split(r'(Day \d+)', text.strip())
    formatted_text = '<div class="workout-routine">'

    for i, item in enumerate(items):
        item = item.strip()

        if item.startswith("Day"):  # Day titles
            if item.strip():  # Ensure the day title is not empty
                # Add the cleaned "Day X" to formatted_text
                formatted_text += f'<div class="day-title">{item}</div>'

        elif item:  # Exercise content
            exercises = item.split("\n")
            for exercise in exercises:
                exercise = exercise.strip()
                if exercise:  # Only add non-empty exercise content
                    formatted_text += f'<div class="exercise-content">{exercise}</div>'  # No symbols, just plain text

    formatted_text += '</div>'
    return formatted_text


def recommend(user_inputs):
    user_BMI, user_experience, user_injury, user_medication = user_inputs

    try:
        # Compute similarity scores
        similarity_BMI = get_similarity(user_BMI, df['BMI'])
        similarity_experience = get_similarity(user_experience, df['Experience Level'])
        similarity_injury = get_similarity(user_injury, df['Injury'])
        similarity_medication = get_similarity(user_medication, df['Medication'])

        total_similarity_all = (
            similarity_BMI +
            similarity_experience +
            similarity_injury +
            similarity_medication
        )

        # Find the best match index
        best_match_idx = total_similarity_all.idxmax()
        recommended_exercises = df.loc[best_match_idx, 'Recommended Exercises']

        # Configure Gemini Model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2000,
            "response_mime_type": "text/plain",
        }

        model = gemini.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

        # Prepare the prompt
        prompt = f"""
You are a professional fitness expert. Based on the following user inputs and recommended exercises, create a comprehensive fitness and diet plan tailored to their needs.

### User Inputs:
- **BMI**: {user_BMI}
- **BMI Category**: {'''if 18.5 <= bmi <= 24.9: bmi_category = "Equal"  elif bmi < 18.5: bmi_category = "Lesser than average"  else: bmi_category = "Greater than average"'''}

- **Experience Level**: {user_experience}
- **Injury**: {user_injury}
- **Medication**: {user_medication}

### Recommended Exercises:
{recommended_exercises}

### Task:
Based on the above inputs, provide the following:

1. **10-Day Workout Routine**: Develop a detailed workout plan for 10 days. Each day's plan must include **2-3 unique exercises** (no repetitions across days). Specify duration or reps/sets for each exercise and provide a brief explanation (2-3 sentences) for each exercise's purpose, benefits, and progression tips. Do not repeat exercises across multiple days. For Day 10, provide a general workout plan or a review of the exercises performed during the previous days.

2. **10 Exercises**: Detail 10 specific exercises that align with the user's profile and goals. For each exercise, include a 2-3 sentence explanation about its execution, benefits, precautions, and progression (e.g., increasing reps or sets).

3. **User Summary**: Write a concise summary (around 50 words) of the user's profile, including their fitness level, potential challenges, and goals based on the input data.


### Output Structure:
- **10-Day Workout Routine**:
  - **Day 1**: [Exercise 1], [Exercise 2], ...
  - (Repeat for Days 2-10)
  - Each exercise should include reps/sets or duration and a brief explanation, including progression tips.

- **10 Exercises**:
  - [Exercise 1]: Explanation, benefits, and progression details.
  - (Repeat for all 10 exercises)

- **User Summary**:
  Provide a clear, concise summary of the user's profile and goals.

"""

        # Generate content using Gemini
        response = model.generate_content(contents=prompt)
        response_text = response.text  # Access the text attribute directly

        # Extract the individual sections
        workout_routine = extract_10_day_workout(response_text)
        exercises = extract_10_exercises(response_text)
        user_summary = extract_user_summary(response_text)
        user_summary = clean_user_summary(user_summary)  # Clean the user summary
  # Clean the user summary

        # Convert to point-wise format where needed
        workout_routine = format_to_pointwise(workout_routine)
        exercises = format_exercises_to_pointwise(exercises)

        # Return structured output
        return {
            "user_summary": user_summary,  # Already concise
            "workout_routine": workout_routine,
            "exercises": exercises,
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "An error occurred while generating recommendations."}