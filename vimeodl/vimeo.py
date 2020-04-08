#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional, Union, Tuple, List, Dict
import pickle
import queue
import os
from pathlib import Path
from time import sleep

import vimeo_dl as vimeo
import requests
from bs4 import BeautifulSoup


from vimeodl import log

__all__ = ["VimeoDownloader"]

__http = requests.Session()


class VimeoLinkExtractor:
    """
    Base class for parsing and extracting
    links from vimeo website
    """

    DOMAIN = "https://vimeo.com/"

    def __init__(self, url):
        self.videos = queue.Queue()
        self.root_url = url.split(self.DOMAIN, maxsplit=1)[1]
        self.waitTime = 1

    def get_content(self, page_soup: BeautifulSoup):
        contents = page_soup.find_all("div", attrs={"id": "browse_content"})
        for content in contents:
            lis = content.find_all("li")
            for li in lis:
                hrefs = li.find_all("a", href=True)
                for href in hrefs:
                    if "/videos/page" not in href["href"]:
                        vid_uri = href["href"].split("/")[-1]
                        log.info("\tLink: {}{}".format(self.DOMAIN, vid_uri))
                        self.videos.put(self.DOMAIN + vid_uri)

    @staticmethod
    def has_next_page(soup: BeautifulSoup) -> bool:
        n = soup.find_all("li", class_="pagination_next")
        if len(n) is 0:
            return False
        if hasattr(n[0], n[0].a.text):
            if n[0].a.text == "Next":
                return True
            return False

    @staticmethod
    def get_next_page(soup: BeautifulSoup) -> Optional[str]:
        if VimeoLinkExtractor.has_next_page(soup):
            n = soup.find_all("li", class_="pagination_next")
            return n[0].a.get("href")
        return None

    def extract(self):
        soup = fetch_page(self.DOMAIN + self.root_url)
        if soup:
            self.get_content(soup)
            while True:
                if self.has_next_page(soup):
                    next_url = self.DOMAIN + self.get_next_page(soup)
                    soup = fetch_page(next_url)
                    sleep(0.2)
                    self.get_content(soup)
                    if self.videos.qsize() % 100 == 0:
                        print("\n[Throttle for {} sec] \n".format(self.waitTime))
                        sleep(self.waitTime)
                else:
                    break
            return list(self.videos.queue)


class VimeoDownloader:
    def __init__(self, url, out_dir, resume):
        self.out_dir = out_dir
        self.resume_file = Path(os.path.join(out_dir, "video_links.p"))
        self.count = 0
        self.total = None
        self.vd = None
        self.urls = list()
        self.url = url
        self.queue = queue.Queue()

        # check if there's a file with links already
        if resume and self.resume_file.is_file():
            log.info("Loading urls from file\n")
            with open(os.path.join(out_dir, "video_links.p"), "rb") as file:
                self.urls = pickle.load(file)
        else:
            log.warning("Can't find resume file")
            log.info("Extracting urls")
            self.vd = VimeoLinkExtractor(self.url)
            self.urls = self.vd.extract()
            log.info("Resume file: " + out_dir + os.sep + "video_links.p")
            with open(os.path.join(out_dir, "video_links.p"), "wb") as file:
                pickle.dump(self.urls, file)

        self.total = len(self.urls)
        log.info("Found {} videos\n".format(self.total))

    def download(self):
        for url in self.urls:  # put all links in a queue
            self.queue.put(url)

        while not self.queue.empty():
            url = self.queue.get()
            video = vimeo.new(url, size=True, basic=True)

            print(
                "Title: {}    - Duration: {} \nUrl: {}".format(
                    video.title, video.duration, url
                )
            )
            streams = video.streams
            log.info("Available Downloads: ")
            for s in streams:  # check available video quality
                log.info(f"{s._itag}/{s._resolution}/{s._extension}")
            best_video = video.getbest()  # select the best quality
            log.info(
                f"Selecting best quality: {best_video._itag}/{best_video._resolution}/{best_video._extension}"
            )

            videopath = Path(
                os.path.join(self.out_dir, video.title + "." + s._extension)
            )

            # check if the video in the link is already downloaded
            if videopath.exists():
                log.info(f"Already downloaded : {url}")
                self.count += 1
            else:
                self.count += 1
                log.info(f"Downloading... {self.count}/{self.total} {videopath}")
                best_video.download(filepath=self.out_dir, quiet=False)

                self.urls.remove(url)  # remove downloaded link from the list
            # save the updated list to a file to resume if something happens
            # from there
            pickle.dump(self.urls, open(self.out_dir + os.sep + "video_links.p", "wb"))

        log.info("Download finished [{}/{}]: ".format(self.count, self.total), end="")
        if self.count == self.total:
            log.info("All videos downloaded successfully ")
            os.remove(self.datadir + os.sep + "video_links.p")
        else:
            log.warning("Some videos failed to download run again")


def fetch_page(url: str) -> BeautifulSoup:
    """
    Return BeautifulSoup object after successfully fetched url
    :param url: Url like string
    :return: BeautifulSoup object of url
    """

    response = __http.get(url)
    if response.status_code != 200:
        response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")
