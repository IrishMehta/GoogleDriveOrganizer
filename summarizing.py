import io
from googleapiclient.http import MediaIoBaseDownload
from transformers import BlipProcessor, BlipForConditionalGeneration, pipeline
from PIL import Image
import PyPDF2
import docx
from mammoth import convert_to_markdown


class Summarizer():
    def __init__(self, service):
        self.service = service

    def download_file(self, file_id, file_name, file_type):
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(file_name, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")

            if file_type in ["jpg", "jpeg", "png"]:
                temp= self.image_captioner(file_name)
                print(f'The summary for {file_name} is {temp}')
                os.remove(file_name)
                return temp
            elif file_type in ["docx","msword"]:
                temp = self.doc_summarizer(file_name)
                print(f'The summary for {file_name} is {temp}')
                os.remove(file_name)
                return temp
            elif file_type == "pdf":
                temp= self.pdf_summarizer(file_name)
                print(f'The summary for {file_name} is {temp}')
                os.remove(file_name)
                return temp
            else:
                print('Couldnt create a summary')
                return 'Miscellaneous'
        except Exception as e:
            print(f"Error downloading or processing file: {str(e)}")
            return 'Error in processing'

    def pdf_summarizer(self, file):


        # Extract text from PDF
        def extract_text_from_pdf(pdf_path):
            text = ""
            try:
                with open(pdf_path, 'rb') as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    for page in reader.pages:
                        text += page.extract_text()
            except Exception as e:
                print(f"Error extracting text from PDF: {str(e)}")
            return text

        text = extract_text_from_pdf(file)
        if not text.strip():
            return "No text was extracted from the PDF."

        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        max_input_length = 1024
        if len(text) > max_input_length:
            text = text[:max_input_length]  # Truncate the text if it's too long
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        return summary

    def doc_summarizer(self, file):


        def extract_text_from_docx(docx_path):
            try:
                doc = docx.Document(docx_path)
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                print(f"Error extracting text from DOCX: {str(e)}")
                return ""

        file_ext = os.path.splitext(file)[1].lower()
        if file_ext == ".docx":
            text = extract_text_from_docx(file)
        else:
            return "Unsupported file format."

        if not text.strip():
            return "No text was extracted from the file."

        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        max_input_length = 1024
        if len(text) > max_input_length:
            text = text[:max_input_length]  # Truncate if too long
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        return summary

    def image_captioner(self, file):

        try:
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            image = Image.open(file)
            inputs = processor(images=image, return_tensors="pt")
            out = model.generate(**inputs)
            caption = processor.decode(out[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            print(f"Error captioning image: {str(e)}")
            return "Error generating caption"