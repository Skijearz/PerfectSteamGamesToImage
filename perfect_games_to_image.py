from __future__ import annotations

import asyncio
import io
import os
import sys
import zipfile

import aiohttp
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

OWNED_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={API_KEY}&steamid={STEAMID}&format=json&include_played_free_games=true&include_appinfo=true&include_extended_appinfo=true&{APPIDS_FILTER}"
GAMES_COVER_TEMPLATE_URL = "https://cdn.akamai.steamstatic.com/steam/apps/{APPID}/header.jpg"
GET_PLAYER_ACHIEVEMENTS_URL = "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={}&key={}&steamid={}"
ACHIEVMENT_BANNER_ICON ="https://community.akamai.steamstatic.com/public/images/profile/achievementIcon.svg"
STEAM_CHECK_FOR_VANITY_URL = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={API_KEY}&vanityurl={URL}"
BACKGROUND_COLOR = (16, 18, 20)
STEAM_VANITY_URL = 1
STEAM_PROFILE_URL = 2
STEAM_ID = 3
HTTP_OK = 200
class PerfectGamesToImage:
    def __init__(self: PerfectGamesToImage,steam_id:str) -> None:
        load_dotenv()
        self.steam_api_key = os.getenv("STEAM_API_KEY")
        self.steam_id = steam_id

    def run_from_non_async(self:PerfectGamesToImage)-> bool:
        return asyncio.run(self.run())


    async def run(self: PerfectGamesToImage) -> bool:
        temp = await self.check_steam_profile_url()
        if temp != STEAM_ID:
            match temp:
                case 1:
                    await self.get_steam_id_from_vanity_profile()
                    if self.steam_id == "":
                        return False
                case 2:
                    url = self.steam_id.split("/")
                    self.steam_id = url[(url.index("profiles")+1)]
                case 0:
                    return False

        all_owned_games = await self.get_all_owned_games_from_steamid()
        if len(all_owned_games) == 0:
            return False
        perfect_games = await self.get_all_perfect_games_of_owned_games(all_owned_games)
        if len(perfect_games) == 0:
            return False
        perfect_games.sort(key=lambda tup: tup[2])
        perfect_games_header_urls = await self.get_header_url_for_perfect_games(perfect_games)
        all_perfect_games_header_images = await self.tasked_create_images_from_url(perfect_games_header_urls)
        if None in all_perfect_games_header_images:
            return False
        finished_perfect_games_images_with_banners = await self.add_banner_to_images(all_perfect_games_header_images,perfect_games)
        finished_images = await self.stitch_images_together(finished_perfect_games_images_with_banners)
        if not await self.save_images_to_zip(finished_images):
            return False
        return True


    async def save_images_to_zip(self: PerfectGamesToImage,images: list)-> bool:
        if not os.path.exists("output"):
            os.mkdir("output")
        try:
            zip_file = zipfile.ZipFile(f"output/{self.steam_id}.zip","w",zipfile.ZIP_DEFLATED)
            for i,image in enumerate(images):
                file_name = f"output/{self.steam_id}_{i}.png"
                image.save(file_name)
                zip_file.write(file_name,arcname=f"{self.steam_id}_{i}.png")
                os.remove(file_name)
            if len(images) > 1:
                images[0].save(f"output/{self.steam_id}.gif",save_all=True,append_images=images[1:],optimize=False,duration =6000, loop=0,disposal=2)
                zip_file.write(f"output/{self.steam_id}.gif",arcname=f"{self.steam_id}.gif")
                os.remove(f"output/{self.steam_id}.gif")
            zip_file.close()
        except (zipfile.BadZipFile):
            for file in os.listdir("output"):
                os.remove(file)
            return False
        else:
            return True

    async def check_steam_profile_url(self: PerfectGamesToImage)-> int:
        if self.steam_id.isnumeric():
            return STEAM_ID
        url = self.steam_id.split("/")
        for parts in url:
            if parts == "profiles":
                return STEAM_PROFILE_URL
            if parts == "id":
                return STEAM_VANITY_URL
        return 0


    async def get_steam_id_from_vanity_profile(self:PerfectGamesToImage) -> None:
        temp = self.steam_id.split("/")
        url = temp[(temp.index("id")+1)]

        try:
            async with aiohttp.ClientSession() as session, session.get(STEAM_CHECK_FOR_VANITY_URL.format(API_KEY=self.steam_api_key,URL=url)) as result:
                if result.status == HTTP_OK:
                    json_data = await result.json()
                    self.steam_id = json_data["response"].get("steamid", "")
                else:
                    self.steam_id = ""
        except aiohttp.ClientConnectorError:
            self.steam_id = ""

    async def get_all_owned_games_from_steamid(self: PerfectGamesToImage)-> list:
        try:
            async with aiohttp.ClientSession() as session, session.get(OWNED_GAMES_URL.format(
                API_KEY = self.steam_api_key,
                STEAMID = self.steam_id,
                APPIDS_FILTER = "")) as result:
                    if result.status == HTTP_OK:
                        all_owned_games = []
                        json_data = await result.json()
                        for _games in json_data["response"]["games"]:
                            all_owned_games.append(_games["appid"])
                        return all_owned_games
                    return []
        except aiohttp.ClientConnectorError:
            return []

    async def add_banner_to_images(self: PerfectGamesToImage,images:list, game_info:list) -> list:
        font = ImageFont.truetype("resources/MotivaSansBold.woff.ttf",15,encoding="unic")
        achievement_banner_icon = Image.open("resources/achievement_icon.png")
        width,height = 304, 142
        width_banner, height_banner = 304,23
        padding = 2

        finished_images = []
        for i,image in enumerate(images):
            image = image.resize((width,height))  # noqa: PLW2901
            image_banner = Image.open("resources/banner_background.png")
            image_banner = image_banner.resize((width_banner,height_banner))
            achievement_number = game_info[i][1]
            text = f"{achievement_number} / {achievement_number} Achievements"
            draw = ImageDraw.Draw(image_banner)
            draw.text((8,2),text=text,fill=(235, 235, 235),font=font)
            new_image_with_banner = Image.new("RGB",(width,height+height_banner+padding+7),BACKGROUND_COLOR)

            new_image_with_banner.paste(image,(0,0))
            new_image_with_banner.paste(image_banner,(0,height+padding))
            new_image_with_banner.paste(achievement_banner_icon,(260,130),achievement_banner_icon)
            finished_images.append(new_image_with_banner)
        return finished_images


    async def stitch_images_together(self: PerfectGamesToImage,images: list) -> list:
        width , heigth = images[0].size
        x_padding = 13
        y_padding = 8
        images_per_row = 4
        images_per_col = 7
        max_width = width*images_per_row + ((images_per_row+1)*x_padding)+1
        max_heigth = heigth*images_per_col + ((images_per_col+1)*y_padding)

        new_image = Image.new("RGB",(max_width,max_heigth),BACKGROUND_COLOR)
        x_offset = x_padding
        y_offset = y_padding
        i = 0
        images_to_save = []
        for number_images,image in enumerate(images, start=1):
            new_image.paste(image,(x_offset,y_offset))
            x_offset += width+x_padding
            i += 1
            if i == images_per_row:
                i = 0
                x_offset = x_padding
                y_offset += heigth+y_padding
            if number_images == images_per_col*images_per_row:
                images_to_save.append(new_image)
                new_image = Image.new("RGB",(max_width,max_heigth),BACKGROUND_COLOR)
                i = 0
                x_offset = x_padding
                y_offset = y_padding
        images_to_save.append(new_image)
        return images_to_save

    async def tasked_create_images_from_url(self: PerfectGamesToImage,image_url_list: list) -> list:
        tasks = []
        for url in image_url_list:
            task = asyncio.ensure_future(self.create_images_from_url(url))
            tasks.append(task)
        return await asyncio.gather(*tasks,return_exceptions=True)


    async def create_images_from_url(self: PerfectGamesToImage,image_url: str)-> Image.Image | None:
        try:
            async with aiohttp.ClientSession() as session, session.get(image_url) as result:
                if result.status == HTTP_OK:
                    buffer = io.BytesIO(await result.read())
                    return Image.open(buffer)
                return None
        except aiohttp.ClientConnectionError:
            return None


    async def get_all_perfect_games_of_owned_games(self: PerfectGamesToImage,all_owned_games: list) -> list:
        tasks = []
        for _appid in all_owned_games:
            task = asyncio.ensure_future(self.identify_perfect_games(_appid))
            tasks.append(task)
        data = await asyncio.gather(*tasks, return_exceptions=True)
        return list(filter(lambda item: item is not None,data))

    async def get_header_url_for_perfect_games(self: PerfectGamesToImage,perfect_games:list)-> list:
        header_urls = []
        for covers in perfect_games:
            header_urls.append(GAMES_COVER_TEMPLATE_URL.format(APPID=covers[0]))
        return header_urls

    async def identify_perfect_games(self: PerfectGamesToImage,appid: str) -> tuple| None:
        try:
            async with aiohttp.ClientSession() as session, session.get(GET_PLAYER_ACHIEVEMENTS_URL.format(appid,os.getenv("STEAM_API_KEY"),self.steam_id)) as res:
                if res.status == HTTP_OK:
                    json_data = await res.json()
                    if not json_data["playerstats"]["success"]:
                        return None
                    if "achievements" not in json_data["playerstats"]:
                        return None
                    for number_achievements,achievements in enumerate(json_data["playerstats"]["achievements"], start=1):  # noqa: B007
                        if achievements["achieved"] == 0:
                            return None
                    name = json_data["playerstats"]["gameName"]
                    return(appid,number_achievements,name)
                return None
        except aiohttp.ClientConnectionError:
            return None


if __name__ == "__main__":
    if len(sys.argv) != 2:  # noqa: PLR2004
        sys.exit(-1)
    steam_id = sys.argv[1]
    app = PerfectGamesToImage(steam_id)
    finished: bool = asyncio.run(app.run())


