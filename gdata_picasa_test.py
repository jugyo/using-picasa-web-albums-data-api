#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gdata.photos.service

gd_client = gdata.photos.service.PhotosService()

user = 'kkohno'

# アルバムの情報を取得
albums = gd_client.GetUserFeed(user=user)

for album in albums.entry:
    print 'Album: title=%s, id=%s' % (
        album.title.text, album.gphoto_id.text)
    
    # 画像の情報を取得
    photos = gd_client.GetFeed(
        '/data/feed/api/user/%s/albumid/%s?kind=photo' % (
            user, album.gphoto_id.text))
    for photo in photos.entry:
        print '    Photo: title=%s, src=%s' % (
            photo.title.text, photo.content.src)
