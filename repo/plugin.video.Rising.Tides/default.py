import urllib,xbmcplugin,xbmcgui,xbmcaddon,xbmcvfs,os,_Edit,re,requests,base64,sys,xbmc
from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
import urllib.parse as urllib_parse

try:
    import json
except:
    import simplejson as json

g_ignoreSetResolved=[]

AddonID   = 'plugin.video.Rising.Tides'
addon = _Edit.addon
addon_version = addon.getAddonInfo('version')
profile = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
icon = xbmcvfs.translatePath(os.path.join('special://home/addons/' + AddonID, 'icon.png'))
home = xbmcvfs.translatePath(addon.getAddonInfo('path'))
favorites = os.path.join(profile, 'favorites')
icon = os.path.join(home, 'icon.png')
FANART = os.path.join(home, 'fanart.jpg')
source_file = os.path.join(profile, 'source_file')
debug = 'true'
if os.path.exists(favorites)==True:
    FAV = open(favorites).read()
else: FAV = []
if os.path.exists(source_file)==True:
    SOURCES = open(source_file).read()
else: SOURCES = []


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.live.RisingTides Lists-%s]: %s" %(addon_version, string))

def makeRequest(url, headers=None):
    try:
        if headers is None:
            headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0'}
        req = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        data = req.text
        data = data.replace("<link>.<link>","<link>http://Ignoreme</link>")
        data = data.replace("<link","<url").replace("</link","</url")
        return data
    except Exception as e:
        addon_log('URL: '+url)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)
            xbmc.executebuiltin("XBMC.Notification(RisingTides,We failed with error code - "+str(e.code)+",10000,"+icon+")")
        elif hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
            xbmc.executebuiltin("XBMC.Notification(RisingTides,We failed to reach a server. - "+str(e.reason)+",10000,"+icon+")")
        return None

def SKindex():
    addon_log("SKindex")
    getData(_Edit.MainBase,'')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def regex_from_to(text, from_string, to_string, excluding=True):
    if excluding:
        try: r = re.search("(?i)" + from_string + r"([\S\s]+?)" + to_string, text).group(1)
        except: r = ''
    else:
        try: r = re.search("(?i)(" + from_string + r"[\S\s]+?" + to_string + ")", text).group(1)
        except: r = ''
    return r

def regex_get_all(text, start_with, end_with):
    r = re.findall("(?i)(" + start_with + r"[\S\s]+?" + end_with + ")", text)
    return r

def getSoup(url, data=None):
    if url is not None:
        if url.startswith('http://') or url.startswith('https://'):
            data = makeRequest(url)
            if not data:
                return None
            if re.search("#EXTM3U", data) or 'm3u' in url:
                return data
    elif data is None:
        if xbmcvfs.exists(url):
            if url.startswith("smb://") or url.startswith("nfs://"):
                copy = xbmcvfs.copy(url, os.path.join(profile, 'temp', 'sorce_temp.txt'))
                if copy:
                    data = open(os.path.join(profile, 'temp', 'sorce_temp.txt'), "r").read()
                    xbmcvfs.delete(os.path.join(profile, 'temp', 'sorce_temp.txt'))
                else:
                    addon_log("failed to copy from smb:")
            else:
                data = open(url, 'r').read()
                if re.match("#EXTM3U", data) or 'm3u' in url:
                    return data
        else:
            addon_log("Soup Data not found!")
            return None
    if not data:
        return None
    return BeautifulSoup(data)


def getData(url, fanart):
    if str(url).startswith('plugin://'):
        try:
            parsed = urllib_parse.urlparse(url)
            params = dict(urllib_parse.parse_qsl(parsed.query))
            inner_url  = urllib_parse.unquote_plus(params.get('url', ''))
            inner_mode = params.get('mode', '')
            if inner_mode == '70':
                getDamiTVMatches(inner_url, fanart)
                return
            elif inner_mode == '71':
                getDamiTVCategories(fanart)
                return
        except Exception as e:
            xbmc.log('[getData] plugin:// dispatch error: {}'.format(e), xbmc.LOGERROR)
        return

    SetViewLayout = "List"
    soup = getSoup(url)

    if isinstance(soup, BeautifulSoup):
        if len(soup('layoutype')) > 0:
            SetViewLayout = "Thumbnail"

        if len(soup('channels')) > 0:
            channels = soup('channel')
            for channel in channels:
                linkedUrl = ''
                lcount = 0
                try:
                    linkedUrl = channel('externallink')[0].string
                    lcount = len(channel('externallink'))
                except: pass
                if lcount > 1: linkedUrl = ''

                name = channel('name')[0].string
                thumbnail = channel('thumbnail')[0].string
                if thumbnail is None:
                    thumbnail = ''

                try:
                    if not channel('fanart'):
                        if addon.getSetting('use_thumb') == "true":
                            fanArt = thumbnail
                        else:
                            fanArt = fanart
                    else:
                        fanArt = channel('fanart')[0].string
                    if fanArt is None:
                        raise Exception()
                except:
                    fanArt = fanart

                try:
                    desc = channel('info')[0].string
                    if desc is None: raise Exception()
                except:
                    desc = ''

                try:
                    genre = channel('genre')[0].string
                    if genre is None: raise Exception()
                except:
                    genre = ''

                try:
                    date = channel('date')[0].string
                    if date is None: raise Exception()
                except:
                    date = ''

                try:
                    credits = channel('credits')[0].string
                    if credits is None: raise Exception()
                except:
                    credits = ''

                try:
                    if linkedUrl == '':
                        addDir(str(name), str(url), 2, thumbnail, fanArt, desc, genre, date, credits, True)
                    else:
                        addDir(str(name), str(linkedUrl), 1, thumbnail, fanArt, desc, genre, date, None, 'source')
                except Exception as e:
                    addon_log('There was a problem adding directory from getData(): ' + str(name))
        else:
            addon_log('No Channels: getItems')
            getItems(soup('item'), fanart)
    elif soup is not None:
        parse_m3u(soup)

    if SetViewLayout == "Thumbnail":
        SetViewThumbnail()


def parse_m3u(data):
    content = data.rstrip()
    match = re.compile(r'#EXTINF:(.+?),(.*?)[\n\r]+([^\n]+)').findall(content)
    total = len(match)
    for other, channel_name, stream_url in match:
        if 'tvg-logo' in other:
            thumbnail = re.search(r'tvg-logo=[\'"](.*?)[\'"]', other)
            thumbnail = thumbnail.group(1) if thumbnail else ''
        else:
            thumbnail = ''
        if 'type' in other:
            mode_type = re.search(r'type=[\'"](.*?)[\'"]', other)
            mode_type = mode_type.group(1) if mode_type else ''
            if mode_type == 'yt-dl':
                stream_url = stream_url + "&mode=18"
            elif mode_type == 'regex':
                url = stream_url.split('&regexs=')
                regexs = parse_regex(getSoup('', data=url[1]))
                addLink(url[0], channel_name, thumbnail, '', '', '', '', '', None, regexs, total)
                continue
        addLink(stream_url, channel_name, thumbnail, '', '', '', '', '', None, '', total)
    xbmc.executebuiltin("Container.SetViewMode(50)")


def getSubChannelItems(name, url, fanart):
    soup = getSoup(url)
    channel_list = soup.find('subchannel', attrs={'name': str(name)})
    items = channel_list('subitem')
    getItems(items, fanart)


def GetSublinks(name, url, iconimage, fanart):
    List = []; ListU = []; c = 0
    all_videos = regex_get_all(url, 'sublink:', '#')
    for a in all_videos:
        if 'LISTSOURCE:' in a:
            vurl = regex_from_to(a, 'LISTSOURCE:', '::')
            linename = regex_from_to(a, 'LISTNAME:', '::')
        else:
            vurl = a.replace('sublink:', '').replace('#', '')
            linename = name
        if len(vurl) > 10:
            c = c+1; List.append(linename); ListU.append(vurl)

    if c == 1:
        try:
            liz = xbmcgui.ListItem(name)
            liz.setInfo(type="Video", infoLabels={"Title": name})
            liz.setArt({'icon': iconimage, 'thumb': iconimage})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=ListU[0], listitem=liz)
            xbmc.Player().play(ListU[0], liz)
        except:
            pass
    else:
        dialog = xbmcgui.Dialog()
        rNo = dialog.select('Select A Source', List)
        if rNo >= 0:
            xbmc.Player().play(str(ListU[rNo]), xbmcgui.ListItem(name))


def getItems(items, fanart):
    total = len(items)
    addon_log('Total Items: %s' % total)
    for item in items:
        isXMLSource = False
        isJsonrpc = False
        try:
            name = item('title')[0].string
            if name is None:
                name = 'unknown?'
        except:
            addon_log('Name Error')
            name = ''

        try:
            url = []
            if len(item('url')) > 0:
                for i in item('url'):
                    if i.string is not None:
                        url.append(i.string)
            if len(item('inputstream')) > 0:
                for i in item('inputstream'):
                    if i.string is not None:
                        url.append(i.string)
            elif len(item('sportsdevil')) > 0:
                for i in item('sportsdevil'):
                    if i.string is not None:
                        url.append('plugin://plugin.video.SportsDevil/?mode=1&amp;item=catcher%3dstreams%26url=' + i.string)
            elif len(item('p2p')) > 0:
                for i in item('p2p'):
                    if i.string is not None:
                        url.append('plugin://plugin.video.p2p-streams/?url=' + i.string + '&amp;mode=1&amp;name=' + name)
            elif len(item('yt-dl')) > 0:
                for i in item('yt-dl'):
                    if i.string is not None:
                        url.append(i.string + '&mode=18')
            elif len(item('utube')) > 0:
                for i in item('utube'):
                    if i.string is not None:
                        if len(i.string) == 11:
                            utube = 'plugin://plugin.video.youtube/play/?video_id=' + i.string
                        else:
                            utube = 'plugin://plugin.video.youtube/play/?playlist_id=' + i.string
                url.append(utube)
            elif len(item('f4m')) > 0:
                for i in item('f4m'):
                    if i.string is not None:
                        if '.f4m' in i.string:
                            f4m = 'plugin://plugin.video.f4mTester/?url=' + urllib.parse.quote_plus(i.string)
                        elif '.m3u8' in i.string:
                            f4m = 'plugin://plugin.video.f4mTester/?url=' + urllib.parse.quote_plus(i.string) + '&amp;streamtype=HLS'
                        else:
                            f4m = 'plugin://plugin.video.f4mTester/?url=' + urllib.parse.quote_plus(i.string) + '&amp;streamtype=SIMPLE'
                url.append(f4m)
            if len(url) < 1:
                raise Exception()
        except Exception as e:
            addon_log('Error <link> element, Passing:' + str(name))
            continue

        isXMLSource = False
        try:
            isXMLSource = item('externallink')[0].string
        except: pass
        if isXMLSource:
            ext_url = [isXMLSource]
            isXMLSource = True
        else:
            isXMLSource = False

        try:
            isJsonrpc = item('jsonrpc')[0].string
        except: pass
        if isJsonrpc:
            ext_url = [isJsonrpc]
            isJsonrpc = True
        else:
            isJsonrpc = False

        try:
            thumbnail = item('thumbnail')[0].string
            if thumbnail is None: raise Exception()
        except:
            thumbnail = ''

        try:
            if not item('fanart'):
                if addon.getSetting('use_thumb') == "true":
                    fanArt = thumbnail
                else:
                    fanArt = fanart
            else:
                fanArt = item('fanart')[0].string
            if fanArt is None: raise Exception()
        except:
            fanArt = fanart

        try:
            desc = item('info')[0].string
            if desc is None: raise Exception()
        except:
            desc = ''

        try:
            genre = item('genre')[0].string
            if genre is None: raise Exception()
        except:
            genre = ''

        try:
            date = item('date')[0].string
            if date is None: raise Exception()
        except:
            date = ''

        regexs = None
        if item('regex'):
            try:
                regexs = parse_regex(item('regex'))
            except:
                pass

        try:
            if len(url) > 1:
                alt = 0
                playlist = list(url)
                if addon.getSetting('add_playlist') == "false":
                    for i in url:
                        alt += 1
                        addLink(i, '%s) %s' % (alt, str(name)), thumbnail, fanArt, desc, genre, date, True, playlist, regexs, total)
                else:
                    addLink('', str(name), thumbnail, fanArt, desc, genre, date, True, playlist, regexs, total)
            else:
                if isXMLSource:
                    ext = str(ext_url[0])
                    if ext.startswith('plugin://') and 'mode=' in ext:
                        parsed_ext = urllib_parse.urlparse(ext)
                        ext_params = dict(urllib_parse.parse_qsl(parsed_ext.query))
                        ext_mode = int(ext_params.get('mode', 1))
                        ext_url_inner = urllib_parse.unquote_plus(ext_params.get('url', ''))
                        addDir(str(name), ext_url_inner, ext_mode, thumbnail, fanart, desc, genre, date, None, 'source')
                    else:
                        addDir(str(name), ext, 1, thumbnail, fanart, desc, genre, date, None, 'source')
                elif isJsonrpc:
                    addDir(str(name), str(ext_url[0]), 53, thumbnail, fanart, desc, genre, date, None, 'source')
                elif url[0].find('sublink') > 0:
                    addDir(str(name), url[0], 30, thumbnail, fanart, '', '', '', '')
                else:
                    addLink(url[0], str(name), thumbnail, fanArt, desc, genre, date, True, None, regexs, total)
        except:
            addon_log('There was a problem adding item - ' + str(name))
    print('FINISH GET ITEMS *****')


def parse_regex(reg_item):
    try:
        regexs = {}
        for i in reg_item:
            key_name = i('name')[0].string
            regexs[key_name] = {}
            try:
                regexs[key_name]['expre'] = i('expres')[0].string or ''
            except:
                pass
            try:
                regexs[key_name]['page'] = i('page')[0].string
            except:
                pass
            for key in ['refer','agent','x-req','x-forward','setcookie','appendcookie','origin',
                        'includeheaders','connection','notplayable','noredirect','cookiejar',
                        'ignorecache','post','rawpost','htmlunescape','readcookieonly']:
                try:
                    regexs[key_name][key] = i(key)[0].string
                except:
                    pass
        regexs = urllib.parse.quote(repr(regexs))
        return regexs
    except:
        return None


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        cleanedparams = paramstring.replace('?', '')
        if paramstring[-1] == '/':
            cleanedparams = cleanedparams[:-1]
        for pair in cleanedparams.split('&'):
            splitparams = pair.split('=')
            if len(splitparams) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


def addDir(name, url, mode, iconimage, fanart, description, genre, date, credits, showcontext=False):
    name = str(name) if name else ''
    url = str(url) if url else ''
    iconimage = str(iconimage) if iconimage else ''
    fanart = str(fanart) if fanart else ''
    description = str(description) if description else ''
    genre = str(genre) if genre else ''

    u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.parse.quote_plus(name) + "&iconimage=" + urllib.parse.quote_plus(iconimage) + "&fanart=" + urllib.parse.quote_plus(fanart)
    if date == '' or date is None:
        date = None
    else:
        description += '\n\nDate: %s' % date
    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon": iconimage, "thumb": iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Genre": genre, "dateadded": date, "credits": str(credits) if credits else ''})
    liz.setProperty("Fanart_Image", fanart)
    if showcontext:
        contextMenu = []
        if showcontext == 'source':
            if str(name) in str(SOURCES):
                contextMenu.append(('Remove from Sources', 'XBMC.RunPlugin(%s?mode=8&name=%s)' % (sys.argv[0], urllib.parse.quote_plus(name))))
        elif showcontext == 'fav':
            contextMenu.append(('Remove from Add-on Favorites', 'XBMC.RunPlugin(%s?mode=6&name=%s)' % (sys.argv[0], urllib.parse.quote_plus(name))))
        if name not in FAV:
            contextMenu.append(('Add to Add-on Favorites', 'XBMC.RunPlugin(%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&fav_mode=%s)' % (sys.argv[0], urllib.parse.quote_plus(name), urllib.parse.quote_plus(url), urllib.parse.quote_plus(iconimage), urllib.parse.quote_plus(fanart), mode)))
        liz.addContextMenuItems(contextMenu)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)


def SetViewThumbnail():
    skin_used = xbmc.getSkinDir()
    if skin_used == 'skin.confluence':
        xbmc.executebuiltin('Container.SetViewMode(500)')
    elif skin_used == 'skin.aeon.nox':
        xbmc.executebuiltin('Container.SetViewMode(511)')
    else:
        xbmc.executebuiltin('Container.SetViewMode(500)')


def addLink(url, name, iconimage, fanart, description, genre, date, showcontext, playlist, regexs, total, setCookie=""):
    contextMenu = []
    name = str(name) if name else ''

    if regexs:
        mode = '14'
    elif url.endswith('&mode=18'):
        url = url.replace('&mode=18', '')
        mode = '18'
    elif url.startswith('magnet:?xt=') or '.torrent' in url:
        if '&' in url and '&amp;' not in url:
            url = url.replace('&', '&amp;')
        url = 'plugin://plugin.video.pulsar/play?uri=' + url
        mode = '14'
    else:
        mode = '14'

    u = sys.argv[0] + "?"
    play_list = False

    if playlist:
        if addon.getSetting('add_playlist') == "false":
            u += "url=" + urllib.parse.quote_plus(url) + "&mode=" + mode
        else:
            u += "mode=13&name=%s&playlist=%s" % (urllib.parse.quote_plus(name), urllib.parse.quote_plus(str(playlist).replace(',', '||')))
            name = name + '[COLOR magenta] (' + str(len(playlist)) + ' items )[/COLOR]'
            play_list = True
    else:
        u += "url=" + urllib.parse.quote_plus(url) + "&mode=" + mode

    if regexs:
        u += "&regexs=" + regexs
    if setCookie != '':
        u += "&setCookie=" + urllib.parse.quote_plus(setCookie)

    if date == '':
        date = None
    else:
        description += '\n\nDate: %s' % date

    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon": "DefaultFolder.png", "thumb": iconimage})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Genre": genre, "dateadded": date})
    liz.setProperty("Fanart_Image", fanart)

    if not play_list:
        if regexs:
            if '$pyFunction:playmedia(' not in urllib.parse.unquote_plus(regexs) and 'notplayable' not in urllib.parse.unquote_plus(regexs):
                liz.setProperty('IsPlayable', 'true')
        else:
            liz.setProperty('IsPlayable', 'true')

    if showcontext:
        contextMenu = []
        if showcontext == 'fav':
            contextMenu.append(('Remove from Add-on Favorites', 'XBMC.RunPlugin(%s?mode=6&name=%s)' % (sys.argv[0], urllib.parse.quote_plus(name))))
        elif name not in FAV:
            fav_params = '%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&fav_mode=0' % (sys.argv[0], urllib.parse.quote_plus(name), urllib.parse.quote_plus(url), urllib.parse.quote_plus(iconimage), urllib.parse.quote_plus(fanart))
            if playlist:
                fav_params += 'playlist=' + urllib.parse.quote_plus(str(playlist).replace(',', '||'))
            if regexs:
                fav_params += "&regexs=" + regexs
            contextMenu.append(('Add to Add-on Favorites', 'XBMC.RunPlugin(%s)' % fav_params))
        liz.addContextMenuItems(contextMenu)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, totalItems=total)


def base64_decode(encoded_str):
    try:
        padding = 4 - len(encoded_str) % 4
        if padding != 4:
            encoded_str += "=" * padding
        return base64.b64decode(encoded_str).decode('utf-8')
    except Exception as e:
        xbmc.log("Base64 decode error: {}".format(str(e)), xbmc.LOGERROR)
        return None


def execute_regex(regex_def):
    try:
        page_url = regex_def.get('page', '')
        expres = regex_def.get('expre', '')
        referer = regex_def.get('refer', '')
        rawpost = regex_def.get('rawpost', '')
        if not page_url or not expres:
            return None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': referer if referer else page_url
        }
        req = urllib.request.Request(page_url, headers=headers)
        page_content = urllib.request.urlopen(req).read().decode('utf-8')
        match = re.search(expres, page_content, re.DOTALL)
        if match:
            result = match.group(1)
            if rawpost and rawpost.startswith('s/'):
                parts = rawpost.split('/')
                if len(parts) >= 3:
                    result = re.sub(parts[1], parts[2], result)
            return result
        return None
    except Exception as e:
        xbmc.log("Error executing regex: {}".format(str(e)), xbmc.LOGERROR)
        return None


def show_changelog_if_updated():
    current_version = addon.getAddonInfo('version')
    version_file = os.path.join(profile, 'last_seen_version')

    # Check last seen version
    last_seen = None
    try:
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                last_seen = f.read().strip()
    except:
        pass

    # Nothing to show if already seen this version
    if last_seen == current_version:
        return

    # Write current version as now seen
    try:
        if not os.path.exists(profile):
            os.makedirs(profile)
        with open(version_file, 'w') as f:
            f.write(current_version)
    except Exception as e:
        xbmc.log('[changelog] Could not write version file: {}'.format(e), xbmc.LOGERROR)

    # Read changelog
    changelog_file = os.path.join(home, 'changelog.txt')
    if os.path.exists(changelog_file):
        try:
            with open(changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.splitlines()
            in_section = False
            section_lines = []
            for line in lines:
                if line.startswith('Version '):
                    if in_section:
                        break
                    if current_version in line:
                        in_section = True
                        section_lines.append(line)
                elif in_section:
                    section_lines.append(line)
            # Fallback: show first version block if current not found
            if not section_lines:
                for line in lines:
                    if line.startswith('Version '):
                        if section_lines:
                            break
                        section_lines.append(line)
                    elif section_lines:
                        section_lines.append(line)
            changelog_text = '\n'.join(section_lines)
        except Exception as e:
            xbmc.log('[changelog] Error reading file: {}'.format(e), xbmc.LOGERROR)
            changelog_text = 'See changelog.txt for details.'
    else:
        changelog_text = 'No changelog available.'

    title = 'Rising Tides v{} — {}'.format(
        current_version,
        'Welcome!' if last_seen is None else "What's New"
    )
    xbmcgui.Dialog().textviewer(title, changelog_text)


def check_for_update():
    try:
        current_version = xbmcaddon.Addon().getAddonInfo('version')
        req = urllib.request.Request('https://mullafabz.xyz/version.txt')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36')
        with urllib.request.urlopen(req, timeout=5) as r:
            latest_version = r.read().decode().strip()

        if latest_version != current_version:
            update = xbmcgui.Dialog().yesno(
                'Update Available',
                'Version [COLOR yellow]' + latest_version + '[/COLOR] is available.\nYou have [COLOR white]' + current_version + '[/COLOR].\n\nUpdate now?'
            )
            if update:
                import threading, zipfile
                zip_url = 'https://mullafabz.xyz/Plugins/K19/Plugins/plugin.video.Rising.Tides/plugin.video.Rising.Tides-' + latest_version + '.zip'
                tmp_zip = xbmcvfs.translatePath('special://temp/plugin.video.Rising.Tides-' + latest_version + '.zip')
                addons_path = xbmcvfs.translatePath('special://home/addons/')

                def do_update():
                    try:
                        xbmcgui.Dialog().notification('Updating', 'Downloading v' + latest_version + '...', xbmcgui.NOTIFICATION_INFO, 10000)
                        req2 = urllib.request.Request(zip_url)
                        req2.add_header('User-Agent', 'Mozilla/5.0')
                        with urllib.request.urlopen(req2, timeout=30) as r:
                            data = r.read()
                        with open(tmp_zip, 'wb') as f:
                            f.write(data)
                        with zipfile.ZipFile(tmp_zip, 'r') as z:
                            z.extractall(addons_path)
                        xbmc.executebuiltin('UpdateLocalAddons')
                        xbmc.sleep(2000)
                        xbmc.executebuiltin('NotifyAll(xbmc,onAddonChanged)')
                        xbmc.sleep(500)
                        xbmcgui.Dialog().notification('Done', 'v' + latest_version + ' installed!', xbmcgui.NOTIFICATION_INFO, 3000)
                        xbmc.sleep(1000)
                        xbmc.executebuiltin('RunAddon(plugin.video.Rising.Tides)')
                    except Exception as e:
                        xbmc.log('[update] Error: ' + str(e), xbmc.LOGERROR)
                        xbmcgui.Dialog().notification('Update Failed', str(e), xbmcgui.NOTIFICATION_ERROR, 5000)

                t = threading.Thread(target=do_update)
                t.daemon = False
                t.start()
                t.join()
    except Exception as e:
        xbmc.log('[check_for_update] Error: ' + str(e), xbmc.LOGERROR)


# ======================================================================
# dami-tv.pro match listing — mode 70
# Categories: basketball, football, cricket, hockey, baseball, rugby,
#             afl, motor-sports, fight, american-football, 24/7-streams
#             Special: popular, live, today, all
#             Combined: live:cricket, today:basketball etc.
# ======================================================================
def getDamiTVMatches(category, fanart):
    import json, urllib.request, datetime, time, re as _re
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'

    cat = str(category).strip().lower()

    if cat == 'popular':
        api_url = 'https://dami-tv.pro/papi/matches/all/popular'
    elif cat == 'live':
        api_url = 'https://dami-tv.pro/papi/matches/live'
    elif cat == 'today':
        api_url = 'https://dami-tv.pro/papi/matches/all-today'
    else:
        api_url = 'https://dami-tv.pro/papi/matches/all'

    try:
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', ua)
        req.add_header('Referer', 'https://dami-tv.pro/')
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        xbmc.log('[getDamiTVMatches] Error: {}'.format(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification('DamiTV', 'Error: {}'.format(e), xbmcgui.NOTIFICATION_ERROR, 5000)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    status_filter = None
    league_filter = None
    title_filter  = None
    id_filter     = None
    team_filter   = None
    cat_filter    = None

    if cat.startswith('title:'):
        title_filter = cat[len('title:'):]
        cat = 'all'
    elif cat.startswith('league:'):
        league_filter = cat[len('league:'):]
        cat = 'all'
    elif cat.startswith('id:'):
        id_filter = cat[len('id:'):]
        cat = 'all'
    elif cat.startswith('team:'):
        team_filter = cat[len('team:'):]
        cat = 'all'
    elif ':' in cat:
        status_filter, cat = cat.split(':', 1)

    # alias 247 → 24/7-streams
    if cat == '247':
        cat = '24/7-streams'

    if cat not in ('all', '', 'popular', 'live', 'today'):
        matches = [m for m in data if m.get('category', '').lower() == cat]
    else:
        matches = data

    if status_filter:
        matches = [m for m in matches if m.get('status', '').lower() == status_filter]
    if league_filter:
        matches = [m for m in matches if league_filter.lower() in m.get('league', '').lower()]
    if title_filter:
        matches = [m for m in matches if title_filter.lower() in m.get('title', '').lower()]
    if id_filter:
        matches = [m for m in matches if id_filter.lower() in m.get('id', '').lower()]
    if team_filter:
        matches = [m for m in matches if
                   team_filter.lower() in m.get('teams', {}).get('home', {}).get('name', '').lower() or
                   team_filter.lower() in m.get('teams', {}).get('away', {}).get('name', '').lower()]

    matches = sorted(matches, key=lambda m: (0 if m.get('status') == 'live' else 1, m.get('date', 0)))

    total = len(matches)
    if total == 0:
        xbmcgui.Dialog().notification('DamiTV', 'No matches found for: ' + cat, xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    for m in matches:
        try:
            match_id   = m.get('id', '')
            title      = m.get('title', 'Unknown')
            status     = m.get('status', '')
            poster     = m.get('poster', '')
            date_ms    = m.get('date', 0)
            league     = m.get('league', '')
            sources    = m.get('sources', [])
            viewers    = m.get('viewers', 0)
            roxie_href = m.get('roxieHref', '')

            if not match_id or not sources:
                continue

            if poster and poster.startswith('/'):
                poster = 'https://dami-tv.pro' + poster

            viewer_tag = ' [COLOR red][B]{} viewers[/B][/COLOR]'.format(viewers) if viewers > 0 else ''
            if status == 'live':
                label = '[COLOR lime][B]LIVE[/B][/COLOR]{} [COLOR white][B]{}[/B][/COLOR] [COLOR yellow][B][{}][/B][/COLOR]'.format(viewer_tag, title, league)
            elif date_ms:
                dt = datetime.datetime.utcfromtimestamp(date_ms / 1000)
                label = '[COLOR white][B]{}[/B][/COLOR] [COLOR yellow][B][{}][/B][/COLOR] [COLOR cyan][B]{}[/B][/COLOR]'.format(title, league, dt.strftime('%a %d %b %H:%M UTC'))
            else:
                label = '[COLOR white][B]{}[/B][/COLOR] [COLOR yellow][{}][/COLOR]'.format(title, league)

            if roxie_href:
                slug = roxie_href.lstrip('/')
                m3u8_name = _re.sub(r'-streams-(\d+)', r'\1', slug) + '.m3u8'
                play_url = 'https://dami-tv.pro/papi/roxie-proxy/{}|Referer=https://dami-tv.pro/&User-Agent={}'.format(m3u8_name, ua)
            else:
                play_url = 'https://dami-tv.pro/live-hls/channel/{}/playlist.m3u8|Referer=https://dami-tv.pro/&User-Agent={}'.format(match_id, ua)

            liz = xbmcgui.ListItem(label)
            liz.setArt({'thumb': poster, 'fanart': fanart if fanart else FANART})
            liz.setInfo('video', {'title': label})
            liz.setProperty('IsPlayable', 'true')

            params = urllib.parse.urlencode({'url': play_url, 'mode': '14'})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), sys.argv[0] + '?' + params, liz, isFolder=False, totalItems=total)

        except Exception as e:
            xbmc.log('[getDamiTVMatches] Error on {}: {}'.format(m.get('id', '?'), e), xbmc.LOGERROR)
            continue

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# ======================================================================
# dami-tv.pro sport categories listing — mode 71
# ======================================================================
def getDamiTVCategories(fanart):
    import json, urllib.request
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
    try:
        req = urllib.request.Request('https://dami-tv.pro/papi/matches/all')
        req.add_header('User-Agent', ua)
        req.add_header('Referer', 'https://dami-tv.pro/')
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        xbmc.log('[getDamiTVCategories] Error: {}'.format(e), xbmc.LOGERROR)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    from collections import OrderedDict
    cats = OrderedDict()
    for m in data:
        cat = m.get('category', 'other')
        if cat not in cats:
            cats[cat] = {'total': 0, 'live': 0}
        cats[cat]['total'] += 1
        if m.get('status') == 'live':
            cats[cat]['live'] += 1

    NAMES = {
        'football': 'Football', 'basketball': 'Basketball', 'cricket': 'Cricket',
        'hockey': 'Hockey', 'baseball': 'Baseball', 'rugby': 'Rugby',
        'afl': 'AFL', 'motor-sports': 'Motor Sports', 'fight': 'Fight/WWE',
        'american-football': 'American Football', '24/7-streams': '24/7 Streams',
    }

    all_live = sum(v['live'] for v in cats.values())
    all_total = sum(v['total'] for v in cats.values())
    live_tag = ' [COLOR red]({} LIVE)[/COLOR]'.format(all_live) if all_live > 0 else ''
    label = '[COLOR white][B]All Sports[/B][/COLOR]{} [COLOR gray]({})[/COLOR]'.format(live_tag, all_total)
    params = urllib.parse.urlencode({'url': 'all', 'mode': '70'})
    liz = xbmcgui.ListItem(label)
    liz.setArt({'thumb': icon, 'fanart': fanart})
    liz.setInfo('video', {'title': 'All Sports'})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), sys.argv[0] + '?' + params, liz, isFolder=True)

    for cat, info in sorted(cats.items()):
        display_name = NAMES.get(cat, cat.replace('-', ' ').title())
        live_tag = ' [COLOR red]({} LIVE)[/COLOR]'.format(info['live']) if info['live'] > 0 else ''
        label = '[COLOR white][B]{}[/B][/COLOR]{} [COLOR gray]({})[/COLOR]'.format(display_name, live_tag, info['total'])
        params = urllib.parse.urlencode({'url': cat, 'mode': '70'})
        liz = xbmcgui.ListItem(label)
        liz.setArt({'thumb': icon, 'fanart': fanart})
        liz.setInfo('video', {'title': display_name})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), sys.argv[0] + '?' + params, liz, isFolder=True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playsetresolved2(url, name, iconimage, setresolved=True):
    import ast, json, binascii

    xbmc.log("=== PLAYSETRESOLVED2 CALLED === URL: {}".format(url), xbmc.LOGDEBUG)

    def hex_decode(hex_string):
        try:
            return binascii.unhexlify(hex_string.strip('"\'') ).decode('utf-8')
        except:
            return hex_string

    liz = xbmcgui.ListItem(label=name if name else '')
    if iconimage:
        liz.setArt({'icon': iconimage, 'thumb': iconimage})

    regexs_data = {}
    if len(sys.argv) > 2:
        params = dict(urllib_parse.parse_qsl(sys.argv[2][1:]))
        if 'regexs' in params:
            try:
                regexs_data = ast.literal_eval(params['regexs'])
            except Exception as e:
                xbmc.log("Error parsing regexs: {}".format(str(e)), xbmc.LOGERROR)

    if url and '$doregex[' in str(url):
        for regex_name in re.findall(r'\$doregex\[([^\]]+)\]', url):
            if regex_name in regexs_data:
                regex_def = regexs_data[regex_name]
                if regex_def.get('page') and '$doregex[' in regex_def.get('page'):
                    for nested_name in re.findall(r'\$doregex\[([^\]]+)\]', regex_def['page']):
                        if nested_name in regexs_data:
                            nested_result = execute_regex(regexs_data[nested_name])
                            if nested_result:
                                regex_def['page'] = regex_def['page'].replace('$doregex[{}]'.format(nested_name), nested_result)
                regex_result = execute_regex(regex_def)
                if regex_result:
                    pattern = '$doregex[{}]'.format(regex_name)
                    if re.match(r'^[0-9a-fA-F]+$', regex_result):
                        url = url.replace(pattern, hex_decode(regex_result))
                    else:
                        url = url.replace(pattern, regex_result)

    # sublink / LISTNAME
    if str(url).startswith('sublink:') or str(url).startswith('LISTNAME:'):
        parts = [p.strip() for p in str(url).split('#') if p.strip()]
        links = []; labels = []
        for part in parts:
            if 'LISTNAME:' in part and 'LISTSOURCE:' in part:
                m = re.search(r'LISTNAME:(.*?)::LISTSOURCE:(.*?)::', part, re.DOTALL)
                if m:
                    labels.append(m.group(1).strip())
                    links.append(m.group(2).strip())
            else:
                links.append(part.replace('sublink:', ''))
                labels.append(str(len(links)))
        if not links:
            return
        if len(links) == 1:
            playsetresolved2(links[0], name, iconimage, setresolved)
        else:
            idx = xbmcgui.Dialog().select('Select A Source', labels)
            if idx >= 0:
                playsetresolved2(links[idx], name, iconimage, setresolved)
        return

    # Hex decode
    url_str = str(url)
    url_before_pipe = url_str.split('|')[0].strip() if '|' in url_str else url_str.strip()
    headers_part = ('|' + '|'.join(url_str.split('|')[1:])) if '|' in url_str else ''

    if re.match(r'^[0-9a-fA-F]+$', url_before_pipe):
        try:
            url = hex_decode(url_before_pipe) + headers_part
        except: pass
    else:
        for hm in re.findall(r'([0-9a-fA-F]{30,})', url_before_pipe):
            try:
                decoded = hex_decode(hm)
                if '://' in decoded:
                    url = url_before_pipe.replace(hm, decoded) + headers_part
                    break
            except: pass

    # Parse headers
    headers = {}
    headers_part = ""
    if '|' in str(url):
        url_parts = str(url).split('|')
        url = url_parts[0]
        headers_str = '|'.join(url_parts[1:])
        for pair in headers_str.split('&'):
            if '=' in pair:
                try:
                    k, v = pair.split('=', 1)
                    headers[k.strip()] = v.strip()
                except: pass
        headers_part = '|' + headers_str

    # Branch 0: dami-tv.pro direct HLS (live-hls or roxie-proxy)
    if 'dami-tv.pro' in url:
        import urllib.request as _ureq, base64 as _b64
        referer = headers.pop('Referer', 'https://dami-tv.pro/')
        ua_val  = headers.pop('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36')
        stream_headers = 'Referer={}&User-Agent={}'.format(referer, ua_val)

        liz.setMimeType('application/vnd.apple.mpegurl')
        liz.setContentLookup(False)
        liz.setProperty('inputstream', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.stream_headers',   stream_headers)
        liz.setProperty('inputstream.adaptive.manifest_headers', stream_headers)

        # Pre-fetch the manifest in Python (server allows first fetch).
        # Inject it directly so inputstream.adaptive never makes a second
        # request to the same URL (which the server 403s).
        try:
            _req = _ureq.Request(url)
            _req.add_header('User-Agent', ua_val)
            _req.add_header('Referer',    referer)
            manifest_text = _ureq.urlopen(_req, timeout=10).read().decode('utf-8')

            # Rewrite relative URLs → absolute so segment fetches still work
            base_url = url.rsplit('/', 1)[0] + '/'
            fixed_lines = []
            for _line in manifest_text.splitlines():
                _stripped = _line.strip()
                if _stripped and not _stripped.startswith('#') and not _stripped.startswith('http'):
                    _line = base_url + _stripped
                fixed_lines.append(_line)
            fixed_manifest = '\n'.join(fixed_lines)

            liz.setProperty('inputstream.adaptive.manifest',
                            _b64.b64encode(fixed_manifest.encode('utf-8')).decode('utf-8'))
            xbmc.log('[DamiTV] Manifest injected ({} bytes)'.format(len(fixed_manifest)), xbmc.LOGDEBUG)
        except Exception as _e:
            xbmc.log('[DamiTV] Manifest pre-fetch failed, falling back: {}'.format(_e), xbmc.LOGERROR)

        liz.setPath(url + '|' + stream_headers)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        return

    # Branch 1: cdn.damitv.live
    if 'cdn.damitv.live' in url:
        import urllib.parse as _uparse
        url = _uparse.unquote(url.strip()).replace(' ', '%20')
        user_agent = headers.pop('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36')
        liz.setMimeType('application/vnd.apple.mpegurl')
        liz.setContentLookup(False)
        liz.setProperty('inputstream', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type', 'hls')
        liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=' + user_agent)
        liz.setPath(url + '|User-Agent=' + user_agent)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        return

    # Branch 2: ClearKey DASH
    if 'key_id' in headers and ('key_val' in headers or ':' in headers.get('key_id', '')):
        key_id  = headers.pop('key_id')
        key_val = headers.pop('key_val', '')
        drm_legacy = 'org.w3.clearkey|{}'.format(key_id) if ':' in key_id else 'org.w3.clearkey|{}:{}'.format(key_id, key_val)
        remaining = '&'.join(['{}={}'.format(k, v) for k, v in headers.items()])
        liz.setMimeType('application/dash+xml')
        liz.setContentLookup(False)
        liz.setProperty('inputstream', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.drm_legacy', drm_legacy)
        if remaining:
            liz.setProperty('inputstream.adaptive.stream_headers', remaining)
            liz.setProperty('inputstream.adaptive.manifest_headers', remaining)
        liz.setProperty('inputstream.adaptive.initial_stream_select', '2')
        liz.setPath(url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        return

    # Branch 3: AES-128 HLS with license server
    if 'license_url' in headers and 'license_auth' in headers:
        import urllib.request as _ureq
        license_url  = headers.pop('license_url').replace('%26', '&')
        license_auth = headers.pop('license_auth')
        try:
            req = _ureq.Request(license_url)
            req.add_header('authorization', license_auth)
            req.add_header('User-Agent', 'Mozilla/5.0')
            key_hex = _ureq.urlopen(req, timeout=10).read().hex()
        except Exception as e:
            xbmc.log("[AES128] Key fetch failed: {}".format(str(e)), xbmc.LOGERROR)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, liz)
            return
        liz.setMimeType('application/vnd.apple.mpegurl')
        liz.setContentLookup(False)
        liz.setProperty('inputstream', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.drm_legacy', 'org.w3.clearkey|{}:{}'.format(key_hex[:32], key_hex))
        liz.setPath(url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        return

    # JSON/DRM
    json_processed = False
    if 'manifestUrl' in str(url) and 'clearkey' in str(url):
        try:
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', str(url))
            if json_match:
                dp = json.loads(json_match.group(0))
                manifest_url = dp.get('manifestUrl', '')
                clearkey_str = dp.get('clearkey', '{}').replace('\\"', '"').replace('\\u0026', '&')
                clearkey_data = json.loads(clearkey_str)
                if manifest_url and clearkey_data and isinstance(clearkey_data, dict):
                    key_id = list(clearkey_data.keys())[0]
                    url = manifest_url + (headers_part if headers_part else '')
                    liz.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    liz.setProperty('inputstream.adaptive.license_key', '{}:{}|R{{SSM}}'.format(key_id, clearkey_data[key_id]))
                    json_processed = True
        except Exception as e:
            xbmc.log("Error processing JSON DRM: {}".format(str(e)), xbmc.LOGERROR)

    # Base64
    if not json_processed and 'ahr0chm6ly9' in str(url).lower() and '.mpd' not in str(url).lower():
        url_lower = str(url).lower()
        b64_start = url_lower.find('ahr0chm6ly9')
        if b64_start != -1:
            encoded_str = str(url)[b64_start:]
            pipe_pos = encoded_str.find('|')
            if pipe_pos != -1:
                encoded_str = encoded_str[:pipe_pos]
            decoded_url = base64_decode(encoded_str)
            if decoded_url:
                url = decoded_url + headers_part if headers_part else decoded_url

    # Re-parse headers
    if '|' in str(url) and not headers:
        url_parts = str(url).split('|')
        url = url_parts[0]
        for pair in '|'.join(url_parts[1:]).split('&'):
            if '=' in pair:
                try:
                    k, v = pair.split('=', 1)
                    headers[k.strip()] = v.strip()
                except: pass

    header_string = '&'.join(['{}={}'.format(k, v) for k, v in headers.items()])
    if header_string:
        liz.setProperty('inputstream.adaptive.stream_headers', header_string)
        liz.setProperty('inputstream.adaptive.manifest_headers', header_string)

    url_lower = str(url).lower()
    if '.mpd' in url_lower or 'format=mpd' in url_lower:
        liz.setMimeType('application/dash+xml')
        liz.setContentLookup(False)
        liz.setProperty('inputstream', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    elif '.m3u8' in url_lower:
        liz.setMimeType('application/vnd.apple.mpegurl')
        liz.setContentLookup(False)
        liz.setProperty('inputstream', 'inputstream.adaptive')
        liz.setProperty('inputstream.adaptive.manifest_type', 'hls')
    else:
        liz.setMimeType('application/vnd.apple.mpegurl')
        liz.setContentLookup(False)

    if '|' in str(url):
        url = str(url).split('|')[0]

    final_url = url + '|' + header_string if header_string else url
    liz.setPath(final_url)
    xbmc.log("Final URL: {}".format(final_url), xbmc.LOGDEBUG)

    if not setresolved:
        xbmc.Player().play(url)
    else:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


# ======================================================================
# Main dispatcher
# ======================================================================
xbmcplugin.setContent(int(sys.argv[1]), 'movies')
try: xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except: pass

params = get_params()

url = None; name = None; mode = None; playlist = None
iconimage = None; fanart = FANART; regexs = None

try: url = urllib.parse.unquote_plus(params["url"])
except: pass
try: name = urllib.parse.unquote_plus(params["name"])
except: pass
try: iconimage = urllib.parse.unquote_plus(params["iconimage"])
except: pass
try: fanart = urllib.parse.unquote_plus(params["fanart"])
except: pass
try: mode = int(params["mode"])
except: pass
try: playlist = eval(urllib.parse.unquote_plus(params["playlist"]).replace('||', ','))
except: pass
try: regexs = params["regexs"]
except: pass

addon_log("Mode: " + str(mode))
if url is not None:
    addon_log("URL: " + str(url.encode('utf-8')))
addon_log("Name: " + str(name))

if mode is None:
    addon_log("Index")
    check_for_update()
    SKindex()

    import threading
    def _delayed_changelog():
        xbmc.sleep(1500)
        show_changelog_if_updated()
    t = threading.Thread(target=_delayed_changelog)
    t.daemon = False  # ← was True; must be False to survive after endOfDirectory()
    t.start()


elif mode == 1:
    addon_log("getData mode1")
    getData(url, fanart)
    if not str(url).startswith('plugin://'):
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 3:
    getSubChannelItems(name, url, fanart)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 14:    
    playsetresolved2(url, name, iconimage, setresolved=True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 30:
    GetSublinks(name, url, iconimage, fanart)

elif mode == 70:
    getDamiTVMatches(url, fanart)

elif mode == 71:
    getDamiTVCategories(fanart)