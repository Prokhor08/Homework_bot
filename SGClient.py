from requests import Session, exceptions
from datetime import datetime
import hashlib
import json

TIMEOUT = 10000

class SGClient:
    def __init__(self):
        self.__s = Session()
        self.__login = False
        self.cur_year = 627079
        self.__s.headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
        self.__s.headers["referer"] = "https://sgo.edu-74.ru/"
        self.__s.headers["origin"] = "https://sgo.edu-74.ru"

    def __del__(self):
        if self.__login == True:
            print("SGClient is logged in while destructor call")

    def login(self, login, password):
        self.login_safe(login, len(password), hashlib.md5(
            password.encode()).hexdigest())

    def login_safe(self, login, password_len, password_hash):
        if self.__login == True:
            raise Exception("SGClient is already logged in")
        text = json.loads(self.__s.post("https://sgo.edu-74.ru/webapi/auth/getdata", cookies={
                          "NSSESSIONID": "fc62e4705768459fa65b99d74145f001"}, timeout=TIMEOUT).text)
        salt = text["salt"]
        pass_hash = hashlib.md5((salt + password_hash).encode()).hexdigest()
        text.pop("salt")
        text["LoginType"] = 1
        text["cid"] = 2
        text["sid"] = 1
        text["pid"] = -1
        text["cn"] = 1
        text["sft"] = 2
        text["scid"] = 51
        text["UN"] = login
        text["PW"] = pass_hash[:password_len]
        text["pw2"] = pass_hash
        text["ver"] = text["ver"]
        dataLT = text["lt"]
        dataVer = text["ver"]
        res = json.loads(self.__s.post("https://sgo.edu-74.ru/webapi/login", headers={
                         'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, data=text, timeout=TIMEOUT).text)
        if "message" in res:
            raise Exception("SG Login error. SG message: '" +
                            res["message"].strip() + "'")
        self.__login = True
        self.__token = res["at"]
        init_text = json.loads(self.__s.get(
            "https://sgo.edu-74.ru/webapi/student/diary/init", headers={'at': self.__token}, timeout=TIMEOUT).text)
        self.__userid = init_text["students"][0]["studentId"]

    def logout(self):
        logout_text = self.__s.post("https://sgo.edu-74.ru/asp/logout.asp", headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={
                                    'at': self.__token, 'VER': int(time() * 1000)}, timeout=TIMEOUT).text
        self.__s.headers.clear()
        self.__s.cookies.clear()
        self.__token = None
        self.__login = False
        self.__userid = None
        self.__s.close()

    def getHomework(self, week_start, week_end):
        homework = json.loads(self.__s.get(
            f'https://sgo.edu-74.ru/webapi/student/diary?studentId={self.__userid}&weekEnd={week_end}&weekStart={week_start}&withLaAssigns=true&yearId={self.cur_year}', headers={'at': self.__token}, timeout=TIMEOUT).text)
        return homework

    def getAttachment(self, id):
        res = self.__s.get(f'https://sgo.edu-74.ru/webapi/attachments/{id}', headers={
                           'at': self.__token}, timeout=TIMEOUT).content
        return res

    def getDescription(self, id):
        res = json.loads(self.__s.get(
            f'https://sgo.edu-74.ru/webapi/student/diary/assigns/{id}?studentId={self.__userid}', headers={'at': self.__token}, timeout=TIMEOUT).content)
        return res

