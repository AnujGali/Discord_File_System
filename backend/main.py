from fastapi import FastAPI, File, UploadFile 
from fastapi.responses import JSONResponse 
import uuid 
import discord 
import os 
import dotenv # can use a token-reading package that reads .env and ports it the ENV variable 
import json 
from io import BytesIO 
from contextlib import asynccontextmanager 
import threading 
import asyncio 

# load the env variables from the .env file 
dotenv.load_dotenv() 
discord_token = os.getenv("DISCORD_BOT_TOKEN") 
superblock_channel_id = int(os.getenv("SUPERBLOCK_CHANNEL_ID")) 
data_channel_id = int(os.getenv("DATA_CHANNEL_ID")) # temporarily will be using only 1 channel to store all the blocks (effectively one directory) TODO: add more directories 

# -----------------------------
# MAIN CODE 
# ----------------------------- 

# Set up the Discord bot client
intents = discord.Intents.default()
client = discord.Client(intents=intents) 

client_loop = None # this is the event loop for the Discord bot 

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}') 

    # read all messages in superblock and add them to a list for later use 

# async function to send all the blocks for a specific file to Discord 
async def send_blocks_to_discord(blocks, file_uuid, filename): 

    print("Sending blocks to Discord...") 
    # loop through each block and send it to Discord
    superblock_channel = client.get_channel(superblock_channel_id) 
    data_channel = client.get_channel(data_channel_id) 

    # check whether file already exists in the FS 
    # if it exists, fully overwrite it 

    # TODO: check if the file already exists in the superblock channel 

    # block metadata: list of message ids and corresponding block number 
    block_metadata = [] 

    # for each block, generate a unique filename and send it to Discord 
    for i, block in enumerate(blocks): 
        # generate a unique filename for each block 
        # format of: "{filename}_{blocknum}" 
        block_filename = f"{filename}_block{i}" 

        # create a discord file object 
        # convert the block to a BytesIO object since Discord requires a file-like object 
        discord_file = discord.File(fp=BytesIO(block), filename=block_filename) 

        # send the file to the Discord channel 
        msg = await data_channel.send(file=discord_file) 

        # add message id to a list for manifest later 
        block_metadata.append({"block_num": i, "channel_id": msg.channel.id, "message_id": msg.id}) 

    # should have sent all the blocks to Discord, so we can send a manifest to the superblock channel 
    # manifest will have a pointer to each message
    # f"File: {filename}\nUUID: {file_uuid}\nBlocks: {len(blocks)}\Locations: {block_metadata}\n" 
    manifest_dict = {
    "filename": filename,
    "uuid": str(file_uuid),
    "num_blocks": len(blocks),
    "blocks": block_metadata
    } 

    manifest_str = json.dumps(manifest_dict, indent=2)

    # send the manifest to the superblock channel 
    await superblock_channel.send(f"File Manifest:\n```json\n{manifest_str}```") 

    # return the manifest 
    return manifest_str 

# we want the Discord bot to startup when FastAPI starts up 
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code 
    # start the async loop for the Discord bot in a separate thread 
    asyncio.ensure_future(client.start(discord_token)) 
    yield # FastAPI will start running here 

# set up the FastAPI app 
# using FastAPI over Flask since it has async support built in 
app = FastAPI(lifespan=lifespan) 

# setup the FastAPI app
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try: 
        # attempt to read the file in 
        file_contents = await file.read() 

        # chunk the file into 8MB chunks
        block_size = 8 * 1024 * 1024 
        blocks = [] 
        for i in range(0, len(file_contents), block_size):
            blocks.append(file_contents[i:i + block_size]) 

        # generate UUID 
        file_uuid = uuid.uuid4() # TODO: maybe generate a UUID dependent on unique piece of the file? Honestly maybe we just use filename as the UUID 

        print("File received is:\n", file_contents) 

        # send all the blocks to Discord alongside UUID, filename? 
        block_send_result = await send_blocks_to_discord(blocks, file_uuid, file.filename) 

        # here we should have all the block uploaded with no issue 

        # return a JSON response to the frontend with success and maybe some metadata 
        return {"message": "File uploaded successfully", "uuid": str(file_uuid), "filename": file.filename} 
    except Exception as e: 
        # error occurred, return a JSON response with error message 
        return {"message": "An error occurred", "error": str(e)} 
