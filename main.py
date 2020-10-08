from datetime import datetime, date, timedelta
import spacetrack.operators as op
from spacetrack import SpaceTrackClient
from pyorbital.orbital import Orbital


import shapefile as sf

# Имя пользователя и пароль
USERNAME = ########
PASSWORD = #########



def get_spacetrack_tle(sat_id, start_date, end_date, username, password, latest=False):
    st = SpaceTrackClient(identity=username, password=password)
    if not latest:
        daterange = op.inclusive_range(start_date, end_date)
        data = st.tle(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle', epoch=daterange)
    else:
        data = st.tle_latest(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle')

    if not data:
        return 0, 0

    tle_1 = data[0:69]
    tle_2 = data[70:139]
    return tle_1, tle_2



def create_orbital_track_shapefile_for_day(sat_id, track_day, step_minutes, output_shapefile):

    if track_day > date.today():
        tle_1, tle_2 = get_spacetrack_tle(sat_id, None, None, USERNAME, PASSWORD, True)

    else:
        tle_1, tle_2 = get_spacetrack_tle(sat_id, track_day, track_day + timedelta(days=1), USERNAME, PASSWORD, False)


    if not tle_1 or not tle_2:
        print('Impossible to retrieve TLE')
        return


    orb = Orbital("N", line1=tle_1, line2=tle_2)

    sf.shapeType = sf.POINT
    track_shape = sf.Writer(output_shapefile)

    track_shape.field('ID', 'N', 40)
    track_shape.field('TIME', 'C', 40)
    track_shape.field('LAT', 'F', 40)
    track_shape.field('LON', 'F', 40)
    i = 0
    minutes = 0
    while minutes < 1440:

        utc_hour = int(minutes // 60)
        utc_minutes = int((minutes - (utc_hour * 60)) // 1)
        utc_seconds = int(round((minutes - (utc_hour * 60) - utc_minutes) * 60))

        utc_string = str(utc_hour) + '-' + str(utc_minutes) + '-' + str(utc_seconds)
        utc_time = datetime(track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)

        lon, lat, alt = orb.get_lonlatalt(utc_time)

        track_shape.point(lon, lat)

        track_shape.record(i, utc_string, lat, lon)


        i += 1
        minutes += step_minutes


    print(1)
    try:

        prj = open("%s.prj" % output_shapefile.replace('.shp', ''), "w")

        wgs84_wkt = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'

        prj.write(wgs84_wkt)

        prj.close()

        track_shape.Save('C:\\test_out')

    except:

        print('Unable to save shapefile')
        return