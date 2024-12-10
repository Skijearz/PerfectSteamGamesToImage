# Perfect Games to Image
Personal tool to visualize all perfect games (games with 100% achievement completed) of a given Steam profile.
There is also a working version hosted on my server, which can be found [here](https://spg.skijearz.xyz).
The Script takes the SteamID of a profile, checks for all perfect games, and creates images of its banner and achievement counts.
It outputs a .zip file with all images and a .gif with all images concatenated in a simple "animation".

# Example gif of my perfect games (28.10.2024) :
![76561198043396026](https://github.com/user-attachments/assets/5cff9d7e-f018-4ebe-aa17-fd8105c85fcc)



# Selfhosting 
1. Get yourself a SteamWebAPI Key. You can create one [here](https://steamcommunity.com/dev/apikey)
2. **Create .env file**: create a `.env` file in the root directory and enter your STEAM_API_KEY:
   ```python
    STEAM_API_KEY = ""
     ```
3. **Start the App**: Either create a Docker container or use the following command:
   ```bash
   python app.py
   ```
Easiest way is to use the attached dockerfile and docker-compose configuration.
