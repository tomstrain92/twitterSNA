import tweepy
from tweepy import OAuthHandler
from geopy.geocoders import Nominatim
import folium
from folium import IFrame
import argparse


def getAPI():
    # instantiation of the twitter api via tweepy
    consumer_key = ''
    consumer_secret = ''
    access_token = ''
    access_secret = ''

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)

    return api


def getFriendIDs(user_handle, api):
    # use twitter api to find users that both follow
    # and are followed by the user_handle name
    # a list of thier twitter ids are returned
    follow_ids = []
    following_ids = []
    print('waiting for tweepy.Cursor API rate limit to refresh')

    for user in tweepy.Cursor(api.followers, screen_name=user_handle,
                              count=100, wait_on_rate_limit=True).items():
        follow_ids.append(user.id)

    for user in tweepy.Cursor(api.friends, screen_name=user_handle,
                              count=100, wait_on_rate_limit=True).items():
        following_ids.append(user.id)

    friend_ids = [id_ for id_ in following_ids if id_ in follow_ids]

    return friend_ids


def getLatLong(location, geolocator):
    # get lat and long co-ords for location from geolocator
    location = location.split('/')[0]
    geo = geolocator.geocode(location)
    return geo.latitude, geo.longitude


def createHTML(name, username, location, information, image):
    # create html for popup on map
    html = """
        <h3 style="font-family:verdana;">{}</h3>
        <h4 style="font-size:10pt; font-family:verdana;">@{}, {}</h4>
        <p style="font-size:10pt;font-family:verdana;">{}</p>
        <img src={}>
        """.format(name, username, location, information, image)
    return html


def plotFriendsOnMap(friend_ids, api):
    # creates map with folium. Geolocations are found by passing
    # user location data to geolocator
    geolocator = Nominatim()
    map = folium.Map([54.783333, -3], zoom_start=5)
    print('getting user information')
    marker_cluster = folium.MarkerCluster().add_to(map)
    # get user information for first 100 "friends" from their ids
    user_profiles = api.lookup_users(user_ids=friend_ids[1:100])
    for user in user_profiles:
        # create html popup for friend and place on map
        html = createHTML(user.name, user.screen_name, user.location,
                          user.description, user.profile_image_url)
        iframe = IFrame(html, width=250, height=150)
        popup = folium.Popup(iframe, max_width=2650)
        # try except incase friend doesn't have location information
        try:
            lat, long = getLatLong(user.location, geolocator)
            folium.Marker([lat, long], popup=popup).add_to(marker_cluster)
            print("plotted {} in {}".format(user.name, user.location))
        except:
            AttributeError

    return map


def main(user_handle):
    print("creating twitter SNA for user {}".format(user_handle))
    api = getAPI()
    friend_ids = getFriendIDs(user_handle, api)
    map = plotFriendsOnMap(friend_ids, api)
    print('saving map in maps/')
    map.save('maps/{}_twitter_social_network.html'.format(user_handle))


if __name__ == '__main__':
    # defining command line parser
    parser = argparse.ArgumentParser(description='Create Social Network from friends found on Twitter and plots them on a map saved in /maps')
    parser.add_argument('user_handle', type=str, help='twitter username for SNA to be performed on')
    args = parser.parse_args()
    main(args.user_handle)