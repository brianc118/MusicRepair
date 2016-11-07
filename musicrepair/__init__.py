#!/usr/bin/env python

from __future__ import print_function
from os import system, rename, listdir, listdir, path
from sys import version_info, stdin, platform
from select import select
from time import sleep


from bs4 import BeautifulSoup
import requests
import json

from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, APIC, USLT
from mutagen.mp3 import EasyMP3 as MP3

if version_info[0] < 3:
    input = raw_input
    from urllib2 import urlopen, Request
    from urllib2 import quote
else:
    from urllib.parse import quote
    from urllib.request import urlopen, Request


def getDetails(songName):

    timeout = 10
    url = "http://search.letssingit.com/cgi-exe/am.cgi?a=search&artist_id=&l=archive&s=" + \
        quote(songName.encode('utf-8'))
    html = requests.get(url)
    soup = BeautifulSoup(html.text, "html.parser")
    link = soup.find('a', {'class': 'high_profile'})
    try:
        link = link.get('href')
        link = requests.get(link)

        soup = BeautifulSoup(link.text, "html.parser")

        AlbumDiv = soup.find('div', {'id': 'albums'})
        TitleDiv = soup.find('div', {'id': 'content_artist'}).find('h1')
        try:
            lyrics = soup.find('div', {'id': 'lyrics'}).text
            lyrics = lyrics[3:]
        except:
            lyrics = "Couldn't find lyrics"

        try:
            songTitle = TitleDiv.contents[0]
            songTitle = songTitle[1:-8]
        except Exception as e:
            print("Couldn't reset song title : %s" % e, end=' ')
            songTitle = songName

        try:
            artist = TitleDiv.contents[1].getText()
        except Exception as e:
            print("Couldn't find artist name : %s" % e, end=' ')
            artist = "Unknown"

        try:
            album = AlbumDiv.find('a').contents[0]
            album = album[:-7]
        except Exception as e:
            print("Couldn't find the album name : %s" % e, end=' ')
            album = artist

    except Exception:
        check = 'n\n'
        print(
            "Couldn't find song details, would you like to manually enter them? (Y/N) : ")
        rlist, _, _ = select([stdin], [], [], 10)
        if rlist:
            check = stdin.readline()
        else:
            print("No input. Moving on.")
            album = songName
            songTitle = songName
            artist = "Unknown"

            return artist, album, songTitle

        if check == 'Y\n' or check == 'y\n':

            album = input("Enter album name : ")
            songTitle = input("Enter song title : ")
            artist = input("Enter song artist : ")

        else:
            album = songName
            songTitle = songName
            artist = "Unknown"

    return artist, album, songTitle, lyrics


def getAlbumArt(album):

    album = album + " Album Art"
    url = ("https://www.google.co.in/search?q=" +
           quote(album.encode('utf-8')) + "&source=lnms&tbm=isch")
    header = {'User-Agent':
              "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
              }

    soup = BeautifulSoup(urlopen(Request(url, headers=header)), "html.parser")

    a = soup.find("div", {"class": "rg_meta"})
    albumArt = json.loads(a.text)["ou"]
    return albumArt


def add_AlbumArt(albumArt, songTitle):
    try:
        img = urlopen(albumArt)  # Gets album art from url
    except:
        print("Could not add album art")
    try:
        audio = MP3(songTitle, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass

        audio.tags.add(
            APIC(
                encoding=3,  # UTF-8
                mime='image/png',
                type=3,  # 3 is for album art
                desc='Cover',
                data=img.read()  # Reads and adds album art
            )
        )
        audio.save()

    except Exception as e:

        print("An Error occured while adding the album art : %s " % e)

        pass


def add_Details(FileName, songTitle, artist, album, lyrics):

    print(" \n\nSong name : %s \n\nArtist : %s \n\nAlbum : %s \n\n " % (
        songTitle, artist, album))

    try:
        tags = ID3(FileName)
        tags["TALB"] = TALB(encoding=3, text=album)
        tags["TIT2"] = TIT2(encoding=3, text=songTitle)
        tags["TPE1"] = TPE1(encoding=3, text="")
        tags["TPE2"] = TPE2(encoding=3, text=artist)
        tags["USLT::'eng'"] = (
            USLT(encoding=3, lang=u'eng', desc=u'desc', text=lyrics))

        tags.save(FileName)

    except Exception as e:

        print("Couldn't add song details : %s" % e)

        pass

    try:
        rename(FileName, songTitle + '.mp3')
    except:
        pass


def search():
    files = [f for f in listdir('.') if f[-4:] == '.mp3']
    for FileName in files:
        tags = MP3(FileName)
        try:
            print("%s already has tags " % tags["album"][0])
        except:

            print("%s Adding metadata" % FileName)
            artist, album, songName, lyrics = getDetails(FileName)
            albumArt = getAlbumArt(album)

            add_AlbumArt(albumArt, FileName)
            add_Details(FileName, songName, artist, album, lyrics)


system('clear')
