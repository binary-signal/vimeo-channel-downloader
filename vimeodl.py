from bs4 import BeautifulSoup
from pathlib import Path
from time import sleep
import vimeo_dl as vimeo
import requests
import argparse
import pickle
import queue
import sys
import os




class VimeoLinkExtractor():
    """
    Base class for parsing and extracting
    links from vimeo website
    """
    def __init__(self, url):
        self.videos = queue.Queue()
        self.domain = "https://vimeo.com/"
        self.root_url = url.split("https://vimeo.com/", 1)[1]
        self.waitTime = 1

    def get_content(self, page_soup):
        contents = page_soup.find_all('div', attrs={'id': 'browse_content'})
        for content in contents:
            lis = content.find_all('li')
            for li in lis:
                hrefs = li.find_all('a', href=True)
                for href in hrefs:
                    if '/videos/page' not in href['href']:
                        vid_uri = href['href'].split("/")[-1]
                        print("\tLink: {}{}".format(self.domain,vid_uri))
                        self.videos.put(self.domain + vid_uri)

    def has_next_page(self, soup):
        n = soup.find_all('li', class_='pagination_next')
        if len(n) is 0:
            return False
        if hasattr(n[0], n[0].a.text):
            if n[0].a.text == "Next":
                return True
            else:
                return False

    def get_next_page(self, soup):
        if self.has_next_page(soup):
            n = soup.find_all('li', class_='pagination_next')
            return n[0].a.get('href')
        else:
            return None

    def extract(self):
        soup = fetch_page(self.domain + self.root_url)
        if soup is not None:
            self.get_content(soup)
            while True:
                if self.has_next_page(soup):
                    next_url = self.domain + self.get_next_page(soup)
                    soup = fetch_page(next_url)
                    self.get_content(soup)
                    if self.videos.qsize() % 100 == 0:
                        print("\n[Throttle for {} sec] \n".format(
                            self.waitTime))
                        sleep(self.waitTime)
                else:
                    break
            return list(self.videos.queue)


class VimeoDownloader:
    def __init__(self, url, out_dir, resume):
        self.out_dir = out_dir
        self.resume_file = Path(out_dir + os.sep + "video_links.p")
        self.count = 0
        self.total = None
        self.vd = None
        self.urls = list()
        self.url = url
        self.links = queue.Queue()

        # check if there's a file with links already
        if resume is True:
            if self.resume_file.is_file():
                print("Loading urls from file\n")
                self.urls = pickle.load(open(out_dir + os.sep
                                             + "video_links.p", "rb"))
            else:
                print("Warning: can't find resume file \n")
                print("Extracting urls")
                self.vd = VimeoLinkExtractor(self.url)
                self.urls = self.vd.extract()
                print("resume file: " + out_dir + os.sep + "video_links.p")
                pickle.dump(self.urls, open(out_dir + os.sep
                                            + "video_links.p", "wb"))
                print("\n")
        else:  # if not fetch the video urls
            print("Extracting urls")
            self.vd = VimeoLinkExtractor(self.url)
            self.urls = self.vd.extract()
            pickle.dump(self.urls, open(out_dir + os.sep
                                        + "video_links.p", "wb"))
            print("\n")

        self.total = len(self.urls)
        print("Found {} videos\n".format(self.total))

    def download(self):
        for url in self.urls:  # put all links in a queue
            self.links.put(url)

        while not self.links.empty():
            url = self.links.get()
            video = vimeo.new(url)

            print("Title: {}    - Duration: {} \nUrl: {}".format(video.title,
                                                                 video.duration,
                                                                 url))
            streams = video.streams
            print("Available Downloads: ", end="")
            for s in streams:  # check available video quality
                print("{}/{}/{}".format(s._itag, s._resolution, s._extension),
                      end=" ")
            print("\n")
            best = video.getbest()  # select the best quality
            print(
                "Selecting best quality: {}/{}/{}".format(best._itag,
                                                          best._resolution,
                                                          best._extension))

            videopath = Path(self.out_dir + os.sep
                             + video.title + "." + s._extension)

            # check if the video in the link is already downloaded
            if videopath.is_file():
                print("Already downloaded : {}\n\n".format(url))
                self.count += 1
            else:
                self.count += 1
                print("Downloading... {}/{} {}\n\n".format(
                    self.count, self.total, videopath))
                best.download(filepath=self.out_dir, quiet=False)


                self.urls.remove(url)  # remove downloaded link from the list
            # save the updated list to a file to resume if something happens
            # from there
            pickle.dump(self.urls, open(self.out_dir + os.sep
                                        + "video_links.p", "wb"))

        print("Download finished [{}/{}]: ".format(self.count, self.total), end="")
        if self.count == self.total:
            print("All videos downloaded successfully ")
            os.remove(self.datadir + os.sep + "video_links.p")
        else:
            print("Some videos failed to download run again")


def fetch_page(url):
    """
    Fetch the page specified by the url and return
    a beautiful soup object of the url fetched
    :param url:
    :return: soup object
    """
    response = requests.get(url)
    if response.status_code == 200:
        response_soup = BeautifulSoup(response.text, 'html.parser')
        return response_soup
    else:
        return None


def check_arg(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('url',
                        metavar='url',
                        type=str,
                        help='vimeo url')

    parser.add_argument('-o', '--save_path',
                        help='save videos to directory',
                        default='.')
    parser.add_argument('-r', '--resume',
                        action='store_true',
                        help='resume download',
                        default='store_false')

    results = parser.parse_args(args)
    return (results.url,
            results.save_path,
            results.resume)

if __name__ == "__main__":
    url, save_path, resume = check_arg(sys.argv[1:])

    if not url.endswith("/videos") or "vimeo.com/" not in url:
        print("Error: Invalid vimeo url")
        print("e.g. https://vimeo.com/vjloop/videos")
        sys.exit(-1)

    vim = VimeoDownloader(url, save_path, resume)
    vim.download()
