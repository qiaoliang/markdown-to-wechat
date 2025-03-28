import os
import json
import requests
from typing import Dict, Tuple
from werobot import WeRoBot


class WxClient:
    def __init__(self):
        self.robot = WeRoBot()
        self.robot.config["APP_ID"] = os.getenv("WECHAT_APP_ID")
        self.robot.config["APP_SECRET"] = os.getenv("WECHAT_APP_SECRET")
        self.sender = self.robot.client

    def get_access_token(self):
        return self.sender.get_access_token()

    def _get_image_type(self, file_path) -> str:
        return "image/" + file_path.split(".")[-1]

    def upload_permanent_media(self, file_path, file_name) -> Tuple[str, str]:
        token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
        files = {
            "media": (file_name, open(file_path, "rb"), self._get_image_type(file_path))
        }
        response = requests.post(url, files=files)
        if response.status_code == 200:
            media_json = response.json()
            media_id = media_json["media_id"]
            media_url = media_json["url"]
        else:
            print(f"请求失败，状态码: {response.status_code}")
            raise Exception(f"请求失败，状态码: {response.status_code}")
        return media_id, media_url

    def upload_article_draft(self, articles: Dict) -> str:
        token = self.get_access_token()
        headers = {"Content-type": "text/plain; charset=utf-8"}
        data = {"articles": articles}
        datas = json.dumps(data, ensure_ascii=False).encode("utf-8")
        postUrl = "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=%s" % token
        r = requests.post(postUrl, data=datas, headers=headers)
        resp = json.loads(r.text)
        print(resp)
        media_id = resp["media_id"]
        print(media_id)
        print("Successfully uploaded, media_id: {}".format(media_id))
        return media_id
