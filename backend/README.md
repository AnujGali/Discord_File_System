# Backend 
The backend was created in Python using the discord.py library. Additionally, I am using FastAPI to facilitate communication between the backend and frontend. 

# How it works 
- The backend receives a payload of the file uploaded/edited by the user from the frontend. 
- It then chunks the payload into blocks and upserts block metadata in the Discord server database. 
- Then, the blocks themselves get uploaded to the backend and a success message is sent to the frontend. 
