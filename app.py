#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
# import class migrate from flask_migrate
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CSRFProtect
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# create an application that gets named after the name of out file, which is app.
app = Flask(__name__)
moment = Moment(app)
csrf = CSRFProtect(app)

# TODO: connect to a local postgresql database
# Flask's config object allows us to assign values to configuration variables, 
# which we'll then have access to throughout our application.
# define the configuration options in the module that calls from_object()
# from_object() loads only the uppercase attributes of the module/class
# app.config.from_object("config_filename.ConfigClass")
# in this case will select DevelopementConfig
app.config.from_object('config.DevelopmentConfig')
# create the SQLAlchemy object by passing it the application and binding it to it.
# links the app to the db or viceversa
db = SQLAlchemy(app)

# link up flask app and db with an instance of the migrate class

# The two arguments to Migrate are the application instance 
# and the Flask-SQLAlchemy 
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'venues'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  # TODO: implement any missing fields, as a database migration using Flask-Migrate
  genres = db.Column(db.String(120))
  website = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.Text())
  # relationship
  shows = db.relationship('Show', backref='venue', lazy=True)

  
    # Relationships
class Artist(db.Model):
  __tablename__ = 'artists'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  # TODO: implement any missing fields, as a database migration using Flask-Migrate
  website = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.Text)
  # relationship
  shows = db.relationship('Show', backref='artist', lazy=True)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

# since we are going to add a start-time column
# The association object pattern is a variant on 
# many-to-many: it’s used when your association 
# table contains additional columns beyond those 
# which are foreign keys to the left and right tables.

class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime(), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)



# we ensure that db tables are created for all the models we declared
# and havn't yet been created
# and that the model is sync with our db

# when we implement migrations we don't need create_all() to sync models with db
# db.create_all()




#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # as some cities are repeated, we will use distinct.
  # The DISTINCT clause is used in the SELECT statement to remove duplicate rows from a result set. 
  areas = []
  try:
    # we save all cities into an array call areas
    for venue in Venue.query.distinct(Venue.city, Venue.state).all():
      city_state = {'city': venue.city, 'state': venue.state}
      areas.append(city_state)
    
    # add venue to areas
    # based on data used, venues is a list of dictionaries
    for a in areas:
      # we loop through all venues that match a city      
      a['venues'] = [{
        'id': v.id,
        'name': v.name,
        # num_shows should be aggregated based on number of upcoming shows per venue.
        'num_upcoming_shows': v.shows
      } for v in Venue.query.filter_by(city=a['city']).all()]
    
    return render_template('pages/venues.html', areas=areas)
  
  except:
    flash('An error occurred. No venues to display currently')
    return redirect(url_for('index'))
    
  
  

@app.route('/venues/search')
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  try:
    search_term = request.args.get('search_term')
    # for case insensitive we can use the ILIKE operator 
    results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response={
      "count": len(results) ,
      "data": [{
        "id": v.id,
        "name": v.name,
        "num_upcoming_shows": len(v.shows)
      } for v in results]
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)

  except:
    flash('An error occurred while searching, please try again')
    return redirect(url_for('venues'))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  past_shows = Show.query.filter(Show.start_time < datetime.now(), Show.venue_id == venue_id).all()
  upcoming_shows = Show.query.filter(Show.start_time >= datetime.now(), Show.venue_id == venue_id).all()
  try:
    # shows the venue page with the given venue_id
    venue = Venue.query.filter_by(id=venue_id).first_or_404()
    data = {
      'id': venue.id,
      'name': venue.name,
      'address': venue.address,
      'city': venue.city,
      'genres': venue.genres,
      'state': venue.state,
      'phone': venue.phone,
      'website': venue.website,
      'facebook_link': venue.facebook_link,
      'seeking_talent': venue.seeking_talent,
      'seeking_description': venue.seeking_description,
      'image_link': venue.image_link,
      # past shows
      'past_shows': [{
        'artist_id': p.artist_id,
        'artist_name': p.artist.name,
        'artist_image_link': p.artist.image_link,
        'start_time': p.start_time.strftime("%m/%d/%Y, %H:%M")
      } for p in past_shows],
      # current/upcomming shows
      'upcoming_shows': [{
        'artist_id': u.artist.id,
        'artist_name': u.artist.name,
        'artist_image_link': u.artist.image_link,
        'start_time': u.start_time.strftime("%m/%d/%Y, %H:%M")
      } for u in upcoming_shows],
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }
    # TODO: replace with real venue data from the venues table, using venue_id
    return render_template('pages/show_venue.html', venue=data)
  except:
    flash('Sorry, we couldn\'t show that venue')
    return redirect(url_for('index'))

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    # add data to db
    new_venue = Venue(
      name = request.form.get('name'),
      city = request.form.get('city'),
      state = request.form.get('state'),
      genres = request.form.getlist('genres'), # string separated by commas
      phone = request.form.get('phone'),
      facebook_link = request.form.get('facebook_link'),
      image_link=request.form.get('image_link'),
      website=request.form.get('website'),
      seeking_talent=request.form.get('seeking_talent') == 'True', # python evaluates False only if empty string. 
      seeking_description=request.form.get('seeking_description')
    )
    db.session.add(new_venue)
    db.session.commit()
  except:
    # rollback if failed.
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    # close session
    db.session.close()

  if not error:
    # on successful db insert, flash success
    # since it was successful we can use request.form
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    # TODO: on unsuccessful db insert, flash an error instead.
    # since it was unsuccessful we can use request object so we use Venue object
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('Venue ' + new_venue.name + ' was not listed.')
  
  # return render_template('pages/home.html')
  return redirect(url_for('index'))

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  error = None
  
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    # query id and delete
    venue = Venue.query.filter_by(id=venue.id)
    venue.delete()
    # commit change
    db.session.commit()
  except:
    error = True
    # if failed, rollback
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  if not error:
    flash('Successfully deleted Venue ' + venue.name)
  else:
    flash('An error ocurred when trying to delete venue ' + venue.name + '. Please try again later.')
  
  return redirect(url_for('index'))


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = [{'id': a.id, 'name': a.name} for a in Artist.query.all()]

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['GET'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  try:
    # get search term from get request. Since its a get, we use args (from url) 
    search_term = request.args.get('search_term', '')
    # we user ilike to get case-insensitive matches to the serach term
    matches = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

    results={
      "count": len(matches),
      "data": [{
        "id": a.id,
        "name": a.name,
        "num_upcoming_shows": 0 # add logic
      } for a in matches]
    }
    return render_template('pages/search_artists.html', results=results, search_term=search_term)
  except:
    flash('Error while searching.')
    return redirect(url_for('artists'))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  try:
    past_shows = Show.query.filter(Show.start_time < datetime.now(), Show.artist_id == artist_id).all()
    upcoming_shows = Show.query.filter(Show.start_time >= datetime.now(), Show.artist_id == artist_id).all()
    # shows the venue page with the given venue_id
    artist = Artist.query.filter_by(id=artist_id).first_or_404()
    # TODO: replace with real venue data from the venues table, using venue_id
    data={
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": [{
        "venue_id": p.venue_id,
        "venue_name": p.venue.name,
        "venue_image_link": p.venue.image_link,
        "start_time": p.start_time.strftime("%m/%d/%Y, %H:%M")
      } for p in past_shows],
      "upcoming_shows": [{
        'venue_id': u.venue.id,
        'venue_name': u.venue.name,
        'venue_image_link': u.venue.image_link,
        'start_time': u.start_time.strftime("%m/%d/%Y, %H:%M")
      } for u in upcoming_shows],
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data) # add methods
  except:
    flash('Sorry, we couldn\'t show that artist')
    return redirect(url_for('index'))

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # first we need to get the artist we want to edit
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  # show data in form
  form = ArtistForm(
    name = artist.name,
    city=artist.city,
    state=artist.state,
    genres=artist.genres,
    phone=artist.phone,
    facebook_link=artist.facebook_link,
    website=artist.website,
    image_link=artist.image_link,
    seeking_venue=artist.seeking_venue,
    seeking_description=artist.seeking_description
  )

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # get artist from db
  try:
    artist = Artist.query.filter_by(id=artist.id).first_or_404()
    
    #set values. Get them from request body
    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form.get('facebook_link')
    artist.website = request.form.get('website')
    artist.image_link = request.form.get('image_link')
    artist.seeking_venue = request.form.get('seeking_venue') == 'True'
    artist.seeking_description = request.form.get('seeking_description')

    # commit changes
    db.session.commit()

  except:
    # if failed rollback
    db.session.rollback()
    flash('An error occurred while editing artist. Please try again later.')
  
  finally:
    db.session.close()
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # we need to get the venue we want to change
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  # get data from venue and show it on venue form
  form = VenueForm(
    name = venue.name,
    city = venue.city,
    state = venue.state,
    address = venue.address,
    phone = venue.phone,
    facebook_link = venue.facebook_link,
    website = venue.website,
    image_link = venue.image_link,
    seeking_talent = venue.seeking_talent,
    seeking_description = venue.seeking_description
  )

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  try:
    # get venue we want to edit Set new values
    venue = Venue.query.filter_by(id=venue_id).first_or_404()
    # set new values
    venue.name = request.form.get('name')
    venue.city=request.form.get('city')
    venue.state=request.form.get('state')
    venue.address=request.form.get('address')
    venue.phone=request.form.get('phone')
    venue.facebook_link=request.form.get('facebook_link')
    venue.website=request.form.get('website')
    venue.image_link=request.form.get('image_link')
    venue.seeking_talent=request.form.get('seeking_talent') == 'True'
    venue.seeking_description=request.form.get('seeking_description')

    # commit changes
    db.session.commit()
    # venue record with ID <venue_id> using the new attributes
   

  except:
    # if failed
    db.session.rollback()
    flash('Error while editing Venue. Please try again later')
  
  finally:
    db.session.close()
  
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False # for message display
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    # add data from form to db
    new_artist = Artist(
      name=request.form.get('name'),
      city=request.form.get('city'),
      state=request.form.get('state'),
      phone=request.form.get('phone'),
      genres=request.form.getlist('genres'),
      facebook_link=request.form.get('facebook_link'),
      image_link=request.form.get('image_link'),
      website=request.form.get('website'),
      seeking_venue=request.form.get('seeking_venue') == 'True',
      seeking_description=request.form.get('seeking_description')
    )

    # add changes
    db.session.add(new_artist)
    # commit changes
    db.session.commit()
  
  except:
    # if it failes
    error = True # message display
    db.session.rollback()
  
  finally:
    db.session.close()


  if not error:
    # on successful db insert, flash success
    # we can use request as it worked
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('There was an error creating ' + new_artist.name + '. Please try again later.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  
  # we need to get all shows from db
  # we query from object shows
  try:
    data = []
    shows = Show.query.all()
    for show in shows:
        venue = Venue.query.filter_by(id=show.venue_id).first_or_404()
        artist = Artist.query.filter_by(id=show.artist_id).first_or_404()
        data.extend([{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        }])
    
    return render_template('pages/shows.html', shows=data)
  except:
    flash('Either there ar no shows to display or an error occured')
    return redirect(url_for('index'))


  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 4,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }]
  

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # TODO: insert form data as a new Show record in the db, instead
  error = False # for message display
  try:
    new_show = Show(
      start_time=request.form.get('start_time'),
      venue_id=request.form.get('venue_id'),
      artist_id=request.form.get('artist_id')
    )
    # add changes
    db.session.add(new_show)
    # commit changes
    db.session.commit()
  
  except:
    error = True
    db.session.rollback()
  
  finally:
    db.session.close()
  
  if not error:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
