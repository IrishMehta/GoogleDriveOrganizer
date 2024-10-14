# GoogleDriveOrganizer
This repository is a demonstration of how we can use automatic captioning models to organize data in google drive without any supervision

The Basic Flow is as follows:
This Python code integrates with Google Drive to list files in a folder, generate summaries using a file summarizer, classify the files using a large language model (LLM), and move them into categorized subfolders based on the classification.
Key Components:

    Google Drive API Setup:
        The code handles authentication with Google Drive API using OAuth credentials (token.json and credentials.json).
        The main folder and the destination folder are defined by their respective folder IDs.

    Listing Files from a Folder:
        The list_files_in_folder function recursively lists all files within a folder (and its subfolders) on Google Drive. It collects file metadata such as name, path, creation/modification dates, and MIME type.

    Summarization and Categorization:
        The get_category function uses the Summarizer class to generate summaries for supported file types (PDF, DOCX, images).
        For each file, an LLM-based classifier (via the Groq API) categorizes the file based on its summary. The file is classified into one of the predefined categories like Accounting, Marketing, Operations, etc.

    File Movement:
        Once categorized, the file is moved to a folder named after the determined category. The create_folder_if_not_exists function ensures that the folder for each category is created if it doesn't already exist.
        The move_file function moves the file to the appropriate subfolder within the destination folder.

    Process:
        For each file in the folder, the code fetches its summary, determines its category using the LLM, and moves the file into a corresponding category folder within the destination folder.


# Setup
1. Clone the repository
2. Install the required packages using the following command:
- `pip install -r requirements.txt`
3. Create a new project in the Google Cloud Console and enable the Google Drive API.
4. Download the credentials.json file and place it in the root directory of the project.
5. Go to Groq playground and get the API key and model ID
6. Run the script using the following command:
- `python main.py`

The arguments for the main.py script are as follows:
- `--source_folder_id`: The ID of the source folder in Google Drive (default: root folder).
- `--destination_folder_id`: The ID of the destination folder in Google Drive (default: root folder).
- `--groq_api_key`: The API key for the Groq API (required for classification).
- `--categories`: A list of categories to classify the files into (default: ["Accounting", "Marketing", "Operations", "Sales", "Technology"]).
- 

# Example
To run the script with the default settings, use the following command:
- `python main.py`
- This will list all files in the root folder of Google Drive, summarize and classify them, and move them into categorized subfolders within the root folder.


# Limitations
- The code currently supports summarization and classification of PDF, DOCX, and image files. Other file types may not be supported.
- The classification model may not be accurate for all types of documents. Fine-tuning the model on specific categories may improve performance.
- The code does not handle file updates or deletions. It only processes files that are present in the source folder at the time of execution.