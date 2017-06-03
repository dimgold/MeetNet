from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
try: import mysql.connector as mdb
except: import MySQLdb as mdb
from kivy.properties import ObjectProperty, ListProperty, StringProperty, BooleanProperty
import sys
from plyer import gps
from kivy.clock import Clock, mainthread
from kivy.uix.relativelayout import RelativeLayout
import time
from mapview.view import MapMarkerPopup
#from plyer import vibrator

def hash_pass(pswd):
    # md5 hash function to store implicit passwords
    import md5
    md = md5.new()
    md.update(str(pswd))
    return md.hexdigest()

class ConnectForm(BoxLayout):
    # main connection window
    user_name = ObjectProperty()
    password = ObjectProperty()
    log_but = ObjectProperty() # login button
    error = ObjectProperty() # error string
    def __init__(self):
        super(ConnectForm, self).__init__()
        try:
            # mysql server connection
            self.cur = con.cursor()
        except:
            self.error.text = "Sorry, bad connection"
    def login(self):
        try:
            username = self.user_name.text
            username = username.replace('"','``').replace("'","``")
            query = "SELECT passhash FROM users WHERE users.user = '%s'" % (username)
            self.cur.execute(query)
            res = self.cur.fetchall()
            if res == []: # checking user existance
                self.error.text = "The user name doesn't exist - please enter your username and click here to try again"
            else:
                hashpass = hash_pass(self.password.text)
                if hashpass == str(res[0][0]): # checking password
                    self.clear_widgets()
                    self.add_widget(UserGroups(username))
                    self.error.text = hashpass + ',' + str(res[0][0])
                else:
                    self.error.text = "The password you entered is not correct - please edit you password and click here to try again"
        except: # ussually mysql error
            self.clear_widgets()
            self.add_widget(ConnectForm())
            self.error.text = "Something went wrong"
    def create_account(self):
        self.clear_widgets()
        self.add_widget(CreateAccount())
    def exit_app(self):
        # close form
        sys.exit()
             
class UserGroups(BoxLayout):
    # select group window - user is login
    welcome_text = ObjectProperty()
    spinner_values = ListProperty() # groups dropdown
    group = ObjectProperty()
    def __init__(self,user_name):
        super(UserGroups, self).__init__()
        self.user_name = user_name
        global globaluser # saving user in global parameter for widgets communitation
        globaluser= user_name
        self.welcome_text.text = "Hello " + self.user_name + " please choose a group to see where your friend are and to chat with them"
        # mysql - groups selection
        try:
            self.cur = con.cursor()
            groups_query = "SELECT user_groups.group FROM user_groups WHERE user_groups.user = '%s' and user_groups.approved = 1" %(self.user_name)
            self.cur.execute(groups_query)
            query_res = self.cur.fetchall()
            groups_values = []
            for g in query_res:
               groups_values.append(str(g[0]))
        except:
            group_values = ['Bad Connection']
        self.spinner_values = groups_values
        
    def create_group(self):
        self.clear_widgets()
        self.add_widget(CreateGroup(self.user_name))
       
    def view_requests(self):
        self.clear_widgets()
        self.add_widget(ViewRequests(self.user_name))

    def send_request(self):
        self.clear_widgets()
        self.add_widget(SendRequest(self.user_name))
        
    def run_map(self):
        # Open Map widget
        if self.group.text !="":
            self.clear_widgets()
            self.add_widget(Showmap(self.group.text,self.user_name))
            
    def logout(self):
        # clears user and moved back to welcome screen
        self.clear_widgets()
        self.add_widget(ConnectForm())


class Showmap(RelativeLayout):
    # map widget
    msg1=ObjectProperty()
    msg0=ObjectProperty()
    msg =ObjectProperty() 
    grouplab =ObjectProperty() 
    mapview = ObjectProperty()
    user_values = ListProperty()
    usersloc = {}
    
    def callback(self, dt):
        # data refresh callback
        self.load_msg() # reload messages
        self.gpar, mlist = self.load_points() # reload points
        if mlist != self.mlist:
            self.mlist = mlist



    
    def __init__(self,group,user):
        super(Showmap,self).__init__()

        self.user = user
        self.group = group
        self.usersloc = {} #user location for future zoom-in
        self.grouplab.text = 'Group '+str(group)
        self.gpar, self.mlist = self.load_points() # load map parameters
        self.mapview.lat = float(self.gpar['clat'])
        self.mapview.lon = float(self.gpar['clon'])
        self.lat = float(self.gpar['clat'])
        self.lon = float(self.gpar['clon'])
        self.mapview.zoom = int(self.gpar['zoom'])
        self.load_msg() # load message
        self.user_values = ['Points Center']            
        for i in self.mlist:
            self.mapview.add_marker(MMarker(i,self.user,False))
            self.user_values.append(i['name'])
            self.usersloc[i['name']]=(float(i['lat']),float(i['lon']))
        
        Clock.schedule_interval(self.callback, mapdelay) #refreshing data callback
               
            
    def goback(self):
        # back to select groups
        user_name = self.user
        self.clear_widgets()
        self.add_widget(UserGroups(user_name))
            
    def load_points(self):
        # loads recent location from db
        mlist = []
        gpar = {'clat':0.0,'clon':0.0,'zoom':'14'} # map global parameters
        try:
        #if 1==1:
            cur=con.cursor()
            query = "SELECT * FROM recent_loc WHERE recent_loc.group = '"+self.group+"'"
            cur.execute(query) #Quering database
            global globalloc
            rows=cur.fetchall()
            ev = {'minlat':9999,'minlon':9999,'maxlat':-9999,'maxlon':-9999}
            for row in rows:
                if not row[5]:
                    pic = 'Storm-Trooper.jpg'
                else: pic = row[5]
                dat = {'lat': row[1],'lon': row[2], 'name':str(row[0]), 'text':'Was here','date':str(row[3]), 'time': str(row[4]), 'pic': str(pic)}
                mlist.append(dat)
                #if globalloc.has_key(row[0]):
                #    if globalloc[row[0]] != dat:
                #        
                globalloc[str(row[0])] = dat
                gpar['clat']+=row[1]
                gpar['clon']+=row[2]
                self.usersloc[str(row[0])] = (row[1],row[2])
                ev = {'minlat':min(dat['lat'],ev['minlat']),'minlon': min(dat['lon'],ev['minlon']), 'maxlat':max(dat['lat'],ev['maxlat']),'maxlon': max(dat['lon'],ev['maxlon'])}
            maxdist = ((ev['maxlat']-ev['minlat'])**2 + (ev['maxlon']-ev['minlon'])**2)**0.5
            gpar['clat'] = str(gpar['clat']/max(len(mlist),1))
            gpar['clon']= str(gpar['clon']/max(len(mlist),1))
            if len(mlist)==0:
                gpar['clat'],gpar['clon'] = str(32.11),str(34.806)
            self.usersloc['Points Center'] = (float(gpar['clat']), float(gpar['clon']))
            
            cur.close()

        except:
            self.msg0.text = 'Something Went Wrong :( '
        return gpar, mlist
    
        

    def load_msg(self):
        # loads group messages - presents only 2 recent
        try:
            cur=con.cursor()
            query = "SELECT * FROM testlab.messages WHERE messages.group = '"+self.group+"' ORDER BY time DESC LIMIT 2"      
            cur.execute(query) #Quering database
            rows=cur.fetchall()  
            msg0,msg1 = ' ',' '
            if len(rows)>0:
                msg1 = str(rows[0][2])+" - "+str(rows[0][0])+" : "+ str(rows[0][3])
                if len (rows)>1:
                    msg0 = str(rows[1][2])+" - "+str(rows[1][0])+" : "+ str(rows[1][3])
            cur.close()

        except:
            msg0 = 'Something Went Wrong'
            msg1 = ' '
        if (self.msg0.text !=  msg0.replace("\n"," ")[:120]) or (self.msg1.text != msg1.replace('\n', " ")[:120]):
            self.msg0.text = msg0.replace("\n"," ")[:120]
            self.msg1.text = msg1.replace('\n', " ")[:120]

        
    def refresh(self):
        # refresh widget - unused
        self.clear_widgets()
        self.add_widget(Showmap(self.group,self.user))


    def send_msg(self,msg):
        # send message from input form to db, and selects new messages
        mes =  msg.text.replace("'",'`')
        try:
            cur=con.cursor()
            query = "INSERT INTO testlab.messages VALUES ('%s','%s','%s','%s')"%(str(self.user),str(self.group), time.strftime('%Y-%m-%d %H:%M:%S'),str(mes)[:250])
            cur.execute(query)
            con.commit()   
            cur.close()
            self.load_msg()
        except:
            self.load_msg()
            self.msg0.text = "Something Went Wrong. Message wasn't sent"
        self.msg.text = ''
        

class MMarker(MapMarkerPopup):
    lab=ObjectProperty()
    pic=ObjectProperty()
    name=StringProperty()
    
    def checkagain(self, dt):
        if self.lat!= globalloc[self.name]['lat'] or self.lon != globalloc[self.name]['lon']:                   
            self.parent.parent.add_marker(MMarker(globalloc[self.name],self.user,self.is_open))
            self.detach()
            Clock.unschedule(self.checkagain)
        #print 'marker callback',self.user


    def __init__(self,dat,user,opened=False):
        super(MMarker,self).__init__()
        self.user = user
        if opened:
            self.is_open = opened
        self.name = dat['name']
        if self.name == self.user:
            self.source = "marker2.png"
        self.lat = dat['lat']
        self.lon =  dat['lon']
        self.lab.text = "[b]%s[/b] \n Was here \n   Date:%s \n Time: %s" % (dat['name'],dat['date'],dat['time'])
        self.pic.source = dat['pic']
        Clock.schedule_interval(self.checkagain,markerdelay) #refreshing data
        


class CreateAccount(BoxLayout):
    # Create new Account Form
    user_name = ObjectProperty()
    password = ObjectProperty()
    pass_var = ObjectProperty()
    pic_url = ObjectProperty()
    allow_loc = BooleanProperty()
    error_msg = ObjectProperty()
    color = [1.0,0.0,0.0,0.8] 
    def create_account(self):
        try:
            self.cur = con.cursor()
            allow_loc = str(int((self.allow_loc.active)))        
            user_name = self.user_name.text
            user_name = user_name.replace('"','``').replace("'","``")
            password = self.password.text
            password = password.replace('"','``').replace("'","``")
            password_hash = hash_pass(password)
            pass_var = self.pass_var.text
            pass_var = pass_var.replace('"','``').replace("'","``")
            pass_var_hash = hash_pass(pass_var)
            pic_url = self.pic_url.text
            pic_url = pic_url.replace('"','``').replace("'","``") 
            user_verification = "SELECT * FROM users WHERE users.user = '%s'" % (user_name)
            self.cur.execute(user_verification)
            query_res = self.cur.fetchall()
            if len(user_name) <= 1:
                self.error_msg.text = 'Error: The Username is invalid'
            elif query_res != []:
                self.error_msg.text = 'Error: The Username you chose already exists'
            elif password == '':
                self.error.msg.text = 'Error: Password is invalid'
            elif password_hash != pass_var_hash:
                self.error_msg.text = 'Error: No match between password and password verification'
            else:
                insert_query = "INSERT INTO testlab.users VALUES ('%s','%s','%s','%s', '%s')" %(user_name,pic_url,password_hash, time.strftime('%Y-%m-%d %H:%M:%S'),allow_loc)            
                self.cur.execute(insert_query)
                con.commit()   
                self.cur.close()
                self.error_msg.text = 'Success!'
        except:
            self.error_msg.text =  "Error: Sorry, bad connection"
        
    def clear_form(self):
        # clears inputs
        self.user_name.text = ''
        self.password.text = ''
        self.pass_var.text = ''
        self.pic_url.text = ''
        self.allow_loc.active = True
        self.error_msg = ''

    def logout(self):
        #back to main
        self.clear_widgets()
        global globaluser
        globaluser = ''
        self.add_widget(ConnectForm())

class CreateGroup(BoxLayout):
    new_group = ObjectProperty()
    feedback_msg = ObjectProperty()
    def __init__(self,user_name):
        super(CreateGroup, self).__init__()
        self.user_name = user_name

    def create_group(self):
        try:
            self.cur = con.cursor()
            new_group = self.new_group.text
            new_group = new_group.replace('"','``').replace("'","``")
            insert_query = "INSERT INTO testlab.user_groups VALUES ('%s','%s','%s','%s', '%s')" %(self.user_name,new_group,'1','1', time.strftime('%Y-%m-%d %H:%M:%S'))
            self.cur.execute(insert_query)
            con.commit()
            self.cur.close()
            self.clear_choice()
            self.feedback_msg.text = "Your new group '%s' was created successfully" %(new_group)
        except:
            self.feedback_msg.text = "Error: Sorry, bad connection"
    def return_to_account(self):
        self.clear_widgets()
        self.add_widget(UserGroups(self.user_name))

    def clear_choice(self):
        self.new_group.text = ''

    def logout(self):
        #back to main
        self.clear_widgets()
        global globaluser
        globaluser = ''
        self.add_widget(ConnectForm())

class SendRequest(BoxLayout):
    req_group = ObjectProperty()
    feedback_msg = ObjectProperty()
    def __init__(self,user_name):
        super(SendRequest, self).__init__()
        self.user_name = user_name

    def join_request(self):
        try:
            self.cur = con.cursor()
            req_group = self.req_group.text
            req_group = req_group.replace('"','``').replace("'","``")
            check_exist_query = "SELECT user_groups.group FROM user_groups WHERE user_groups.group = '%s'" %(req_group)
            self.cur.execute(check_exist_query)
            query_res = self.cur.fetchall()
            if len(query_res) == 0:
                self.clear_choice()
                self.feedback_msg.text = "Error: Sorry, the group you chose doesn't exist"
            else:
                request_query = "SELECT user_groups.approved FROM user_groups WHERE user_groups.user = '%s' and user_groups.group = '%s'" %(self.user_name, req_group)
                self.cur.execute(request_query)
                query_res = self.cur.fetchall()
                if len(query_res) != 0:
                    if str(query_res[0][0]) == '1':
                        self.clear_choice()
                        self.feedback_msg.text = "Error: You are already a part of this group"
                    else:
                        self.clear_choice()
                        self.feedback_msg.text = "Error: You already sent a request to join this group\nYou'll have to wait for the group's admin approval"
                else:
                    insert_query = "INSERT INTO testlab.user_groups VALUES ('%s','%s','%s','%s', '%s')" %(self.user_name,req_group,'0','0', time.strftime('%Y-%m-%d %H:%M:%S'))
                    self.cur.execute(insert_query)
                    con.commit()
                    self.cur.close()
                    self.clear_choice()
                    self.feedback_msg.text = "Your request to join the group '%s' was sent to the group's admins" %(req_group)
        except:
            self.feedback_msg.text = "Error: Sorry, bad connection"

    def return_to_account(self):
        self.clear_widgets()
        self.add_widget(UserGroups(self.user_name))

    def clear_choice(self):
        self.req_group.text = ''

    def logout(self):
        #back to main
        self.clear_widgets()
        global globaluser
        globaluser = ''
        self.add_widget(ConnectForm())


class ViewRequests(BoxLayout):
    error_msg = ObjectProperty
    title = ObjectProperty
    def __init__(self,user_name):
        super(ViewRequests, self).__init__()
        self.user_name = user_name
        self.req_lst = []
        self.view_requests()

    def view_requests(self):
        try:
            self.cur = con.cursor()
            requests_query = "SELECT user_groups.user, user_groups.group FROM user_groups WHERE user_groups.approved = '0' and user_groups.group IN(SELECT user_groups.group FROM user_groups WHERE user_groups.user = '%s' and user_groups.admin = '1')" %(self.user_name)
            self.cur.execute(requests_query)
            query_res = self.cur.fetchall()
            if len(query_res) == 0:
                self.title.text = "You don't have any requests to approve at this moment"
                self.add_widget(BackNav() )
            else:
                for req in query_res:
                    self.req_lst.append((req[0],req[1]))
                self.add_requests()
                self.add_widget(BackNav())
        except:
            self.error_msg.text = "Error: Sorry, bad connection"

    def add_requests(self):
        for req in self.req_lst:
            self.add_widget(Request(req))

    def return_to_account(self):
        self.clear_widgets()
        self.add_widget(UserGroups(self.user_name))

    def logout(self):
        #back to main
        self.clear_widgets()
        global globaluser
        globaluser = ''
        self.add_widget(ConnectForm())

        
class Request(BoxLayout):
    friend_req = ObjectProperty
    def __init__(self,req):
        super(BoxLayout,self).__init__()
        self.request_user = req[0]
        self.request_group = req[1]
        self.friend_req.text = "The User '%s' Wants to join the group '%s'" %(self.request_user, self.request_group)

    def approve_req(self):
        try:
            update_approvel = "UPDATE user_groups SET user_groups.approved = '1' WHERE user_groups.user = '%s' and user_groups.group = '%s'" %(self.request_user,self.request_group)
            cur = con.cursor()
            cur.execute(update_approvel)
            con.commit()
            self.parent.status_msg.text += "The Request of the user '%s' to join the group '%s' was approved" %(self.request_user,self.request_group)
            self.clear_widgets()
        except:
            self.parent.status_msg.text = "Error: Sorry, bad connection"

    def decline_req(self):
        try:
            delete_row = "DELETE FROM user_groups WHERE user_groups.user = '%s' and user_groups.group = '%s'" %(self.request_user,self.request_group)
            cur = con.cursor()
            cur.execute(delete_row)
            con.commit()
            user_name = self.parent.user_name
            print user_name
            self.parent.status_msg.text += "The Request of the user '%s' to join the group '%s' was declined\n" %(self.request_user,self.request_group)
            self.clear_widgets()
        except:
            self.parent.status_msg.text = "Error: Sorry, bad connection"



class BackNav(BoxLayout):
    pass



class kivyApp(App):

    lat = StringProperty()
    lon = StringProperty()

    def build(self):
        self.user = ''
        self.gps = gps
        Clock.schedule_interval(self.call_send,gpsdelay)
        try:
            self.gps.configure(on_location=self.on_location)
            self.gps.start()
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            self.speed = 'GPS is not implemented for your platform'

    def call_send(self,dt):
        self.send_loc()
        print 'called'

    def send_loc(self):
        try:
            self.cur = con.cursor()
            tm = time.strftime('%Y-%m-%d %H:%M:%S')
            self.tup = (globaluser,self.lat,self.lon,tm)
            if self.lat != '' and self.lon !='' and self.lon !='No access to GPS' and globaluser!='':
                query = "INSERT INTO locations (user,lat,lon,time) VALUES "
                query = query + str(self.tup)
                print query
                self.cur.execute(query)
                con.commit()
            else:
                print 'gotcha'
        except: pass

    @mainthread
    def on_location(self, **kwargs):
        self.lat = str(kwargs.items()[3][1])
        self.lon = str(kwargs.items()[2][1])
        tm = time.strftime('%Y-%m-%d %H:%M:%S')
        self.tup = (globaluser,self.lat,self.lon,tm)




if __name__ == '__main__':
    # main thread
    try:
        with open('cred.txt','r') as pf:
            hst = pf.readline().strip()
            us = pf.readline().strip()
            ps = pf.readline().strip()
            db = pf.readline().strip()
            print hst,us,ps,db
        con = mdb.connect(host=hst ,user=us,passwd= ps, db =db)
    except:
        print 'no connection'
    #mysql connector
    globaluser = '' #current user
    globalloc = {} #current fetched locations
    markerdelay =20.001 # markers refresh rate
    mapdelay = 20.000 #map refresh rate
    gpsdelay = 10.000 # gps refresh rate
    kivyApp().run() # run app
    
