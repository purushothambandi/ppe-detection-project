import face_recognition
import os
import pickle
import time

print("Starting face encoding...")

# Path to the directory of known faces
KNOWN_FACES_DIR = "known_faces"

# Lists to hold the encodings and their names/roles
known_encodings = []
known_names_roles = []

# Loop through each folder (each person) in the known_faces directory
for folder_name in os.listdir(KNOWN_FACES_DIR):
    person_folder_path = os.path.join(KNOWN_FACES_DIR, folder_name)
    
    # Check if it's a directory
    if not os.path.isdir(person_folder_path):
        continue

    print(f"[INFO] Processing person: {folder_name}")
    
    # Loop through each image of this person
    for filename in os.listdir(person_folder_path):
        image_path = os.path.join(person_folder_path, filename)
        
        try:
            # Load the image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations (we assume one face per training image)
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) > 0:
                # Get the encoding for the face
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                
                # Add the encoding and the folder_name (Name_Role) to our lists
                known_encodings.append(encoding)
                known_names_roles.append(folder_name)
                print(f"  - Added encoding from {filename}")
            else:
                print(f"  - [WARNING] No face found in {filename}. Skipping.")
        
        except Exception as e:
            print(f"  - [ERROR] Failed to process {filename}: {e}")

# Save the encodings and names to a file
encoding_data = {
    "encodings": known_encodings,
    "names_roles": known_names_roles
}

with open("face_encodings.pkl", "wb") as f:
    pickle.dump(encoding_data, f)

print("Face encoding complete. Saved to face_encodings.pkl")