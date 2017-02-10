import os
import sys
import urllib
import urlparse
import xbmcaddon
import xbmcgui
import xbmcplugin
import requests
import re

playlist_url = 'http://freezone.internode.on.net/freezone-radio-playlist.list'
raw_rss_url = 'http://freezone.internode.on.net/rss/freezone-radio-raw.rss'

#TODO: add favorites

def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)
    
def build_station_list(stations):
    #TODO: add additional directories for each category
    directory = []
    # iterate over the list of stations to build the directory items for Kodi
    for station in stations:
        # create a list item using the song filename for the label
        li = xbmcgui.ListItem(label=station['title'], thumbnailImage=station['thumb'])
        # set the fanart to the albumc cover
        li.setProperty('fanart_image', station['thumb'])
        # set the list item to playable
        li.setProperty('IsPlayable', 'true')
        # build the plugin url for Kodi
        # Example: plugin://plugin.audio.example/?url=http%3A%2F%2Fwww.theaudiodb.com%2Ftestfiles%2F01-pablo_perez-your_ad_here.mp3&mode=stream&title=01-pablo_perez-your_ad_here.mp3
        url = build_url({'mode': 'stream', 'url': station['link'], 'title': station['title']})
        # add the current list item to a list
        directory.append((url, li, False))
    # add list to Kodi per Martijn
    # http://forum.kodi.tv/showthread.php?tid=209948&pid=2094170#pid2094170
    xbmcplugin.addDirectoryItems(addon_handle, directory, len(directory))
    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)

def unesc_html(text):
    #TODO: replace with character for each code
    return re.sub(r"&.*?;", "", text)

def parse_raw_rss(text, checklist):
    # parse rss text into array of dicts
    stations = []
    index = 1
    for m in re.finditer(r"<item>(.*?)</item>", text, re.DOTALL):
        station = {}
        item = m.group(1)
        m = re.search(r"<title><!\[CDATA\[(.*)\]\]></title>", item)
        if m:
            station['title'] = unesc_html(m.group(1))
        m = re.search(r"<link>(.*)</link>", item)
        if m:
            station['link'] = m.group(1)
        m = re.search(r"<description><!\[CDATA\[(.*)\]\]></description>", item, re.DOTALL)
        if m:
            station['description'] = re.sub(r"<img .*>\n", "", m.group(1))
        m = re.search(r'<thumb url="(.*?)".*/>', item)
        if m:
            station['thumb'] = m.group(1)
        m = re.search(r"<category>(.*)</category>", item)
        if m:
            station['category'] = m.group(1)

        # only append if station is in the checklist
        if station['link'] in checklist:
            stations.append(station)
    
    return stations
    
def play_station(url):
    # set the path of the song to a list item
    play_item = xbmcgui.ListItem(path=url)
    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    
def main():
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    
    # initial launch of add-on
    if mode is None:
        # get a list of working station urls from the playlist_url file
        checklist = [x.split('=')[1] for x in requests.get(playlist_url).text.split('\n') if '=' in x]
        # get list of stations from the raw_rss file checked against the checklist
        stations = parse_raw_rss(requests.get(raw_rss_url).text, checklist)
        # display the list of stations in Kodi
        build_station_list(stations)
        
    # a station from the list has been selected
    elif mode[0] == 'stream':
        print "Playing radio stream '%s' %s" % (args['title'][0], args['url'][0])
        play_station(args['url'][0])
    
if __name__ == '__main__':
    addon_handle = int(sys.argv[1])
    main()
