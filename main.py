from flask import Flask, request, render_template 
import json, bcrypt, datetime, flask
from better_profanity import profanity

app = Flask(__name__, static_url_path='/static')   

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
  app,
  key_func=get_remote_address,
  default_limits=["200 per day", "50 per hour", "15 per minute", "5 per second"]
)

@app.route("/limited")
@limiter.limit("15 per minute", methods=["GET", "POST"])
def five():
  if request.method == "POST":
    return {"response": 429, "success": False, "error": "Too many requests! Slow down!"}
  return "You're rate limited!"

@app.route('/')
def index():
  with open("templates/storage/users.json", "r") as f:
    data = json.load(f)
  with open("templates/storage/qotd.json", "r") as f:
    qotd = json.load(f)
  userinputs = []
  for qotds in qotd:
    if qotd.get(qotds) in [":boohoo:", ":detailedtroll:", ":nah:", ":pepesimp:", ":sad:", ":salute:", ":troll:", ":whatever:"]:
      if ":boohoo:" in qotd.get(qotds):
        newstr = qotd.get(qotds).replace(":boohoo:", "<img src='static/emojis/boohoo.png' width=20px height=20px>")
        userinputs.append(f"{qotds.capitalize()} - \"{newstr}\"")
    else:
      userinputs.append(f"{qotds.capitalize()} - \"{qotd.get(qotds).capitalize()}\"")
  return render_template("index.html", users=len(data), qotdarray=userinputs)

@app.route('/signup', methods =["GET", "POST", "PUT"])
def signup():
  warning = ""
  if request.method == "POST":
    username = request.form.get("fname")
    password = request.form.get("lname")
    all_ascii = ''.join(chr(k) for k in range(128))  # 7 bits
    all_chars = ''.join(chr(k) for k in range(256))  # 8 bits
    all_ascii.replace(":", "")
    for element in username:
      if element not in all_ascii + all_chars:
        return render_template("/frontend/security/signup.html", warning = "Your username must not contain NON ascii characters!")
    with open("templates/storage/users.json", "r") as f:
      data = json.load(f)

    for user in data:
      if username == data[user]['username']:
        return render_template("/frontend/security/signup.html", warning = "That username is taken! Please choose another!")
    
    if len(password) < 8:
      return render_template("/frontend/security/signup.html", warning = "Your password must be at least 8 characters!")
    elif len(username) < 3:
      return render_template("/frontend/security/signup.html", warning = "Your username must be at least 3 characters!")
    elif len(username) > 25:
      return render_template("/frontend/security/signup.html", warning = "Your username must be under 25 characters!!")
    if profanity.contains_profanity(username):
      print(profanity.contains_profanity(username))
      return render_template("/frontend/security/signup.html", warning = "Your username contains blacklisted word(s)!")
    elif username in data:
      return render_template("/frontend/security/signup.html", warning = f"That username ({data[request.access_route[0]]['username']}) is taken!")
    
    elif request.access_route[0] in data:
      print(username)
      return render_template("/frontend/security/signup.html", warning=f"You already have an account ({data[request.access_route[0]]['username']}) registered!")
    with open("templates/storage/users.json", "w") as f:
      data[request.access_route[0]] = {"username": username, "password": bcrypt.hashpw(str(password).encode('utf8'), bcrypt.gensalt()).decode('utf8'),"pfp": f"/static/userpfps/default.png", "notifications": []}
      json.dump(data, f, indent=2)
    dascript = """
      setTimeout(() => {
        window.location.href = 'https://chatocity.ksiscute.repl.co/home'
      }, 5000)
      """
    return f"""
  <html>
    <head>
      <title>Account Created</title>
    </head>
    <body style='font-family: arial;background: #4652af;color: white;'>
      <h1 style='text-align:center'>Welcome {username.capitalize()}!</h1>
      <br>
      <p style='text-align:center'>Your password is {password}, dont forget it!</p>
      <a href='https://flaskpasswordthingy.ksiscute.repl.co/home'>Go Home</a>
      <a href='https://flaskpasswordthingy.ksiscute.repl.co/login'>Login</a>
      <h1>This page redirects you to the homepage automatically in 5 seconds</h1>
    </body>
      <script>
        {dascript}
      </script>
  </html>
      """
  return render_template("/frontend/security/signup.html", warning=warning)

@app.route("/login", methods=["GET", "POST"])
def login():
  print(request.access_route[0])
  
  if request.method == "POST":
    username = request.form.get("loginname")
    password = request.form.get("loginpass")
    print(password)
    print(username)
    with open("templates/storage/users.json", "r") as f:
      data = json.load(f)


    if request.access_route[0] not in data:
      return render_template("/frontend/security/login.html", error="You don't have a registered account in our database!.")
    userpw = bytes(data[request.access_route[0]]["password"].encode())
    for user in data:
      userpw = bytes(data[user]["password"].encode())
      if username.lower() == data[user]['username'].lower():
        if user != request.access_route[0]:
          return render_template("/frontend/security/login.html", error="Login is correct, but from a different ip! For 100% Encryption, ChatOcity requires you to be on the same ip address you were on when you registered. This will be removed soon because of better encryption. But for now this is our policy, sorry!")
        print(data[user]['password'])
        bcrypt.checkpw(bytes(password, encoding="utf8"), data[user]['password'].encode())
        if bcrypt.checkpw(bytes(password, encoding="utf8"), userpw):
          profilephoto = data[request.access_route[0]]['pfp']
          return flask.redirect("/home", code=200)
      else:
        print("Not it")
    
    else:
      return render_template("/frontend/security/login.html", error="Username or Password Incorrect")
  return render_template("/frontend/security/login.html", error="")

@app.route("/home", methods=["GET", "POST"])
def home():
  with open("templates/storage/users.json", "r") as f:
    data = json.load(f)
  if request.method == "POST":
    response = request.form.get("qotdresponse")
    with open("templates/storage/qotd.json", "r") as f:
      qotds = json.load(f)
    if data[request.access_route[0]]['username'] in qotds:
      return render_template('frontend/home.html', qotdnote="You've already answered todays QOTD!")
    with open("templates/storage/qotd.json", "w") as f:
      qotds[data[request.access_route[0]]['username']] = response
      json.dump(qotds, f, indent=2)
    return render_template('frontend/home.html', qotdnote="Thanks for answering todays QOTD!", date=datetime.datetime.now().strftime("%A %B %d, %Y"), username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']))
  if request.access_route[0] in data:
    x = datetime.datetime.now()
    return render_template('frontend/home.html', date=x.strftime("%A %B %d, %Y"), username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']))
  else:
    return render_template('frontend/security/signup.html', warning="""You dont have an account registered in our database!""")
# 
#⠀⠀⠘⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⠀⠀⠀
#⠀⠀⠀⠑⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡔⠁⠀⠀⠀
#⠀⠀⠀⠈⠢⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠴⠊⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠤⠄⠒⠈⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠘⣀⠄⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠔⠒⠒⠒⠒⠒⠢⠤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⡰⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⢄⡀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⡸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠙⠄⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⢀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠃⠀⢠⠂⠀⠀⠘⡄⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠈⢤⡀⢂⠀⢨⠀⢀⡠⠈⢣⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⢀⢀⡖⠒⠶⠤⠭⢽⣟⣗⠲⠖⠺⣖⣴⣆⡤⠤⠤⠼⡄⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠘⡈⠃⠀⠀⠀⠘⣺⡟⢻⠻⡆⠀⡏⠀⡸⣿⢿⢞⠄⡇⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⢣⡀⠤⡀⡀⡔⠉⣏⡿⠛⠓⠊⠁⠀⢎⠛⡗⡗⢳⡏⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⢱⠀⠨⡇⠃⠀⢻⠁⡔⢡⠒⢀⠀⠀⡅⢹⣿⢨⠇⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⢸⠀⠠⢼⠀⠀⡎⡜⠒⢀⠭⡖⡤⢭⣱⢸⢙⠆⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⡸⠀⠀⠸⢁⡀⠿⠈⠂⣿⣿⣿⣿⣿⡏⡍⡏⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⢀⠇⠀⠀⠀⠀⠸⢢⣫⢀⠘⣿⣿⡿⠏⣼⡏⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⣀⣠⠊⠀⣀⠎⠁⠀⠀⠀⠙⠳⢴⡦⡴⢶⣞⣁⣀⣀⡀⠀⠀⠀⠀⠀
#⠀⠐⠒⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⢀⠤⠀⠀⠀⠀⠀⠀⠀⠈⠉⠀⠀⠀⠀⠀
# sorry i want to keep this professional -css
@app.route("/settings", methods=["GET", "POST"])
def settings():
  with open("templates/storage/users.json", "r") as f:
    data = json.load(f)
  x = datetime.datetime.now()
  
  if request.method == "POST":
    imagefile = flask.request.files.get('profilephoto', '')   
    imagefile.save(f"static/userpfps/{data[request.access_route[0]]['username'].capitalize()}.png")
    with open("templates/storage/users.json", "w") as f:  
      data[request.access_route[0]]['pfp'] = f"/static/userpfps/{data[request.access_route[0]]['username'].capitalize()}.png"
      json.dump(data, f, indent=2)
    return render_template('frontend/settings.html', date=x.strftime("%A %B %d, %Y"), username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']), pfp=data[request.access_route[0]]['pfp'], note="Profile photo changed!")
  if request.access_route[0] in data:
    return render_template('frontend/settings.html', date=x.strftime("%A %B %d, %Y"), username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']), pfp=data[request.access_route[0]]['pfp'])
  else:
    return render_template('frontend/security/signup.html', warning="You dont have a registered account! Please create one!")

@app.errorhandler(404)
def pagenotfound(e):
  if request.method == "POST":
    return {"response": 404, "success": False, "error": f"Page {e} does not exist"}
  return render_template('404.html'), 404

@app.route("/api", methods=["GET", "POST"])
@limiter.limit("5 per second")
def api():
  with open("templates/storage/users.json", "r") as f:
    data = json.load(f)
  if request.method == "POST":
    if "username" in request.args:
      username = request.args.get("username")
      user1 = username.replace("'", "")
      user2 = user1.replace('"', "")
      return {"response": 200, "success": True,  "error": False, "username": user2}
    else:
      return {"response": 400, "success": False, "error": "Missing argument: username"}
  return render_template("frontend/api.html", username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']), pfp=data[request.access_route[0]]['pfp'])

@app.route("/api/users", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def getusers():
  with open("templates/storage/users.json", "r") as f:
    data = json.load(f)
  if request.method == "POST":
    userarray = []
    for user in data:
      userarray.append(data[user]['username'])
    return {"response": 200, "success": True, "error": False, "usercount": len(data), "userarray": userarray}
  return render_template("frontend/api.html", username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']), pfp=data[request.access_route[0]]['pfp'])

@app.route("/api/create", methods=["GET", "POST"])
@limiter.limit("5 per day")
def createacc():
  if request.method == "POST":
    with open("templates/storage/users.json", "r") as f:
      data = json.load(f)
    if "username" in request.args:
      if "password" in request.args:
        username = request.args.get("username")
        password = request.args.get("password")
    for user in data:
      if data[user]['username'].lower() == username.lower():
        return {"response": 409, "success": False, "error": "Conflicts: Username already exists"}
      elif request.access_route[0] in data:
        return {"response": 409, "success": False, "error": "Conflicts: Account already registered under IP"}
    else:
      with open("templates/storage/users.json", "w") as f:
        data[request.access_route[0]] = {"username": username, "password": bcrypt.hashpw(str(password).encode('utf8'), bcrypt.gensalt()).decode('utf8'),"pfp": f"/static/userpfps/default.png", "notifications": []}
        json.dump(data, f, indent=2)
      return {"response": 200, "success": True, "error": False, "username": username, "password": password}
  else:
    return render_template("frontend/api.html", username=data[request.access_route[0]]["username"].capitalize(), ncount=len(data[request.access_route[0]]['notifications']), pfp=data[request.access_route[0]]['pfp'])

@app.route("/forum", methods=["GET", "POST"])
def forum():
  with open("templates/storage/forum.json", "r") as f:
    threads = json.load(f)
  forumarray = []
  for i in threads:
    forumarray.append(f"{threads[i]['threadname']}, {threads[i]['threadid']}")
  return render_template("forum.html", forumdata=forumarray)

app.register_error_handler(404, pagenotfound)
if __name__=='__main__':
  app.run(host='0.0.0.0', port=8080)