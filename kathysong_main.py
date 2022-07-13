
# Imports
import tkinter as tk  # Tkinter imports
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import tkinter.font as font
from tkinter.scrolledtext import ScrolledText
from pydub import AudioSegment # Audio processing imports
from pydub.playback import play
import simpleaudio as sa
import datetime # Assorted imports
import time
import os
import random
import multiprocessing

BUTTONBACKGROUNDCOLOR = '#dddd00' # General color scheme
BUTTONTEXTCOLOR = '#335500'

# Below are one function, one original class (the 'song' object), and eight
# tkinter window child classes.  Of the seven window classes, the PlayWindow
# class contains most of the code pertinent to playing the identification game,
# while the GameEditWindow and SongEditWindow for setting up the game.

def simplify(words): # Removes punctuation and capitalization from a phrase.
    def alfilter(char): # Used to compare song title to guess in 'strict' mode,
        if char in "abcdefghijklmnopqrstuvwxyz ":
            return True # e.g. "Don't Stop Believin'" => "dont stop believin"
        return False
    return ''.join(filter(alfilter,words.lower())).strip()

class Song(): # A song object combines a song file location and relevant data
    def __init__(self, titles, artist, hint, fileloc, start, duration):
        self.titles = [titles[0]]
        for title in titles: # Subtitles of a song are considered optional;
            if "(" in title and ")" in title and title.index("(") < title.index(")"):
                self.titles.append(simplify(title[:title.index("(")]+title[title.index(")"):]))
            self.titles.append(simplify(title)) # e.g. "(Sittin' On) The Dock of the Bay"
        self.artist = artist # could be entered as "the dock of the bay" or
        self.hint = hint     # "sittin on the dock of the bay" in strict mode.
        if os.path.isfile(fileloc):
            self.fileloc = fileloc
        else: # This error does not typically occur, as the file is checked elsewhere.
            messagebox.showerror("Song not found",f"Song not found:  {fileloc}")
        self.start = start
        self.duration = duration

    def compare(self,guess,strictness):
        guess = simplify(guess)
        if strictness == 'strict':
            if guess in self.titles:
                return True
            return False
        elif strictness == 'inclusive':
            for title in self.titles:
                if title in guess: # Inclusive mode allows a guesser to include words,
                    return True # e.g. "Hit Me Baby One More Time" when the title is
                if title[-2:] == "in": # "Baby One More Time."
                    if title.replace("in ","ing ") + "g" in guess:
                        return True # Exceptions are also made for dropped g's,
                elif title.replace("in ","ing ") in guess: # which the player may
                    return True # omit or include just the game.
                if title[-3:] == "ing":
                    if title.replace("ing ","in ")[:-1] in guess:
                        return True
                elif title.replace("ing ","in ") in guess:
                    return True
            return False
        elif strictness == 'loose':
            for title in self.titles + [self.artist]: # Loose mode allows one to
                successful = True # guess the artist (at least, the one whom the
                for word in title.split(" "): # maker credits), to omit articles,
                    if word not in guess and word not in ['a','an','the'] and word[:-1] not in guess and word + "g" not in guess:
                        successful = False # to omit any last letter and to add
                if successful: # a 'g' to any word.
                    return True
            return True

    def get_writeable(self): # For writing a song object in a file.
        return '\n'.join([self.fileloc,'|'.join(self.titles),self.artist,self.hint,str(self.start),str(self.duration)])

    def get_waveobject(self): # Yields the playable WaveObject (from the Simpleaudio module)
        if self.fileloc[-1] == '3':
            songas = AudioSegment.from_mp3(self.fileloc)
        else:
            songas = AudioSegment.from_wave_file(self.fileloc)
        songas[self.start:self.start+self.duration].export("temp.wav",format='wav')
        return sa.WaveObject.from_wave_file("temp.wav")

class NameGetWindow(tk.Toplevel): # Puts a player's name on the appropriate
    def __init__(self, labeltochange, master=None, number=0, place=0):
        tk.Toplevel.__init__(self, master) # nametag in the PlayWindow and
        self.title("Insert name") # asks the player to practice buzzing in
        self.resizable(False,False) # with a certain key (depending on position).
        self.iconbitmap('.\Music\KathySong.ico')
        self.config(bg='yellow')
        self.grab_set()
        self.labeltochange = labeltochange
        self.readytochange = tk.BooleanVar(value=False)

        tk.Label(self,text=f'Contestant #{number}, what is your name?',bg='yellow',font=PLAY_MENU_FONT).grid(column=0,row=0)
        namebox_entry = ttk.Entry(self,font=PLAY_MENU_FONT)
        namebox_entry.grid(column=0, row=1)
        namebox_entry.insert(0,random.choice(['Johann','Wolfgang','Ludwig','Louis','Elvis','Michael']))

        self.namebox_entry = namebox_entry

        self.bind('<Return>', lambda e:  self.readytochange.set(True))
        if place == 0:
            tk.Label(self,text='When you have entered your name, press enter and buzz in with the left shift key.',bg='yellow',font=PLAY_MENU_FONT).grid(column=0,row=2)
            self.bind('<Shift_L>', lambda e: self.submit(e))
        elif place == 1:
            tk.Label(self,text='When you have entered your name, press enter and buzz in with the space bar.',bg='yellow',font=PLAY_MENU_FONT).grid(column=0,row=2)
            self.bind('<space>', lambda e:  self.submit(e))
        elif place == 2:
            tk.Label(self,text='When you have entered your name, press enter and buzz in with the right shift key.',bg='yellow',font=PLAY_MENU_FONT).grid(column=0,row=2)
            self.bind('<Shift_R>', lambda e:  self.submit(e))

        self.protocol('WM_DELETE_WINDOW',self.on_exit) # This method is added to
                           # every window class to prevent the game from getting
    def submit(self, e):   # stuck when someone presses 'x' on a custom dialog or
        if self.readytochange.get(): # main screen.
            self.labeltochange.config(text=self.namebox_entry.get())
            self.destroy()

    def on_exit(self):
        self.labeltochange.config(text=self.namebox_entry.get())
        #self.labeltochange.config(text="Can't follow instructions",font=font.Font(family='Segoe Print',size=10))
        self.destroy()

class AnswerWindow(tk.Toplevel): # Retrieves a player's song title guess and
    def __init__(self, playername, master, songobject, strictness):
        tk.Toplevel.__init__(self,master) # evaluates it, modifying the main
        self.config(bg='yellow') # label on the PlayWindow (master) accordingly.
        self.songobject = songobject # Master must be a PlayWindow object.
        self.strictness = strictness
        self.title = f"{playername} has buzzed in"
        tk.Label(self,text=f"{playername}, what is your answer?",bg='yellow',font=PLAY_MENU_FONT).pack()
        ans_ent = ttk.Entry(self,font=PLAY_MENU_FONT)
        ans_ent.pack()
        tk.Label(self,text="Press enter to submit",bg='yellow',font=PLAY_MENU_FONT).pack()
        self.ans_ent = ans_ent
        self.bind('<Return>', lambda e: self.submit(e, strictness))
        self.protocol('WM_DELETE_WINDOW',self.on_exit)

    def submit(self, e, strictness):
        guess = self.ans_ent.get()
        if self.songobject.compare(guess,strictness):
            correct = True
        else:
            correct = False
        correctans, detail = self.songobject.titles[0], self.songobject.artist
        if correct:
            self.master.mainlabeltext.set(f"⭕CORRECT⭕\n{correctans}\n{detail}")
        else:
            self.master.mainlabeltext.set(f"{correctans}\n{detail}")
        self.destroy()

    def on_exit(self): # Assume incorrect if 'x' is hit.
        self.master.mainlabeltext.set(f"{self.songobject.titles[0]}\n{self.songobject.artist}")
        self.destroy()

class PlayWindow(tk.Toplevel): # Plays the game assigned to it by the MainMenuWindow.
    def __init__(self, master, acceptance, number_of_contestants, game=[]):
        tk.Toplevel.__init__(self, master)
        self.title("Play window")
        self.resizable(False,False)
        swid, shei = self.winfo_screenwidth()-20, self.winfo_screenheight() - 100
        self.geometry(f"{swid}x{shei}")
        self.iconbitmap('.\Music\KathySong.ico')
        self.config(bg='yellow')
        self.acceptance = acceptance
        self.number_of_contestants = {'single':1,'dual':2,'triple':3}[number_of_contestants]
        self.game = game
        if self.number_of_contestants == 1:
            self.cont_exist = [False,True,False]
        elif self.number_of_contestants == 2:
            self.cont_exist = [True,False,True]
        elif self.number_of_contestants == 3:
            self.cont_exist = [True, True, True]
        self.buzzin = [tk.BooleanVar(value=False),tk.BooleanVar(value=False),tk.BooleanVar(value=False)]
        self.buzzed = tk.BooleanVar(value=False)
        self.scores = [0, 0, 0]
        self.times = [0.0, 0.0, 0.0]

        for i in range(3):
            self.columnconfigure(i, weight=1)
        self.rowconfigure(0,weight=0)
        self.rowconfigure(1,weight=2)
        self.rowconfigure([2,3],weight=1)

        self.mainlabeltext = tk.StringVar()
        self.mainlabeltext.set('')

        mainlabel = tk.Label(master=self, textvariable=self.mainlabeltext, font=MAIN_PLAY_FONT, bg='blue')
        mainlabel.grid(row=0,column=0,columnspan=3,rowspan=2)
        lcon_lbl = tk.Label(master=self, text="", font=PLAYER_NAME_FONT, bg='green')
        lcon_lbl.grid(row=2,column=0)
        ccon_lbl = tk.Label(master=self, text="", font=PLAYER_NAME_FONT, bg='green')
        ccon_lbl.grid(row=2,column=1)
        rcon_lbl = tk.Label(master=self, text="", font=PLAYER_NAME_FONT, bg='green')
        rcon_lbl.grid(row=2,column=2)
        lsco_lbl = tk.Label(master=self, text="", font=PLAYER_SCORE_FONT, bg='yellow')
        lsco_lbl.grid(row=3,column=0)
        csco_lbl = tk.Label(master=self, text="", font=PLAYER_SCORE_FONT, bg='yellow')
        csco_lbl.grid(row=3,column=1)
        rsco_lbl = tk.Label(master=self, text="", font=PLAYER_SCORE_FONT, bg='yellow')
        rsco_lbl.grid(row=3,column=2)

        self.labellist = [mainlabel,lcon_lbl,ccon_lbl,rcon_lbl,lsco_lbl,csco_lbl,rsco_lbl]

        tk.Button(self, text="Return to main menu", bg='yellow',command=lambda: self.supreme_destroy()).grid(row=0,column=2,sticky=tk.NE)
        tk.Button(self, text="Pass this song", bg='yellow',command=lambda: self.passong()).grid(row=1,column=2,sticky=tk.NE)

        self.protocol('WM_DELETE_WINDOW', self.supreme_destroy)

    def supreme_destroy(self): # This method ends any wait_variable() methods
        for i in range(3): # present elsewhere in the class and returns the
            self.buzzin[i].set(self.buzzin[i].get()) # main menu to view.
        self.buzzed.set(self.buzzed.get()) # Preferable to the 'x' button.
        self.master.deiconify()
        self.destroy()

    def namefill(self):
        for number in range(self.number_of_contestants):
            if self.number_of_contestants == 1:
                place = 1
            elif self.number_of_contestants == 2:
                if number == 0:
                    place = 0
                else:
                    place = 2
            elif self.number_of_contestants == 3:
                place = number
            namewindow = NameGetWindow(self.labellist[place+1], self, number+1, place)
            namewindow.grab_set()
            self.wait_window(namewindow)
            self.grab_set()

    def lbuzz(self, e):
        self.labellist[1].config(bg='white')
        self.buzzin[0].set(True)
        self.buzzed.set(True)

    def cbuzz(self, e):
        self.labellist[2].config(bg='white')
        self.buzzin[1].set(True)
        self.buzzed.set(True)

    def rbuzz(self, e):
        self.labellist[3].config(bg='white')
        self.buzzin[2].set(True)
        self.buzzed.set(True)

    def unbuzz(self):
        for i in range(3):
            self.labellist[i+1].config(bg='green')
            self.buzzin[i].set(False)
        self.buzzed.set(False)

    def get_all_buzzes(self):
        self.mainlabeltext.set('All players buzz in to start round')
        self.bind('<Shift_L>', lambda e: self.lbuzz(e))
        self.bind('<space>', lambda e: self.cbuzz(e))
        self.bind('<Shift_R>', lambda e: self.rbuzz(e))
        for c in range(3):
            if self.cont_exist[c] and not self.buzzin[c].get():
                self.wait_variable(self.buzzin[c])
        self.unbuzz()
        self.mainlabeltext.set('All players buzzed in!')

    def passong(self):
        self.buzzed.set(True)

    def scoreupdate(self):
        for c in range(3):
            if self.cont_exist[c]:
                score = self.scores[c]
                time = self.times[c]
                self.labellist[c+4].config(text=f"{score} songs\nin {time:.2f} seconds")

    #def timerout(self,round_id):
    #    time.sleep(7)
    #    if self.still_waiting and self.round_id == round_id:
    #        self.buzzed.set(True)

    def dosong(self,songobject):
        self.mainlabeltext.set(songobject.hint)
        audioinstance = songobject.get_waveobject().play()
        starttime = time.time()
        #self.round_id = random.random()
        #self.still_waiting = True
        self.bind('<Shift_L>', lambda e: self.lbuzz(e))
        self.bind('<space>', lambda e: self.cbuzz(e))
        self.bind('<Shift_R>', lambda e: self.rbuzz(e))
        #self.timerout(self.round_id)
        self.wait_variable(self.buzzed)
        if audioinstance.is_playing():
            endtime = time.time()
        else:
            endtime = starttime + int(songobject.duration)/1000
        sa.stop_all()
        if self.buzzin[0].get():
            guessername = self.labellist[1].cget('text')
            guesserid = 0
        elif self.buzzin[1].get():
            guessername = self.labellist[2].cget('text')
            guesserid = 1
        elif self.buzzin[2].get():
            guessername = self.labellist[3].cget('text')
            guesserid = 2
        else:
            guesserid = -1 # The song has been passed in this case.
        if guesserid > -0.5:
            self.labellist[0].config(text=guessername)
            answindow = AnswerWindow(guessername,self,songobject,self.acceptance)
            answindow.grab_set()
            self.wait_window(answindow)
        self.unbuzz()
        if len(self.labellist[0].cget('text')) > 0 and self.labellist[0].cget('text')[0] == '⭕':
            self.scores[guesserid] += 1 # Using this text to evaluate could - in a rare case -
            self.times[guesserid] += endtime - starttime # make any wrong guess counted as right
        else:                                            # if the song title begins with the
            self.scores[guesserid] -= 1                  # red circle emoji.
            self.times[guesserid] += endtime - starttime
        self.scoreupdate()

    def run_game(self):
        self.namefill()
        self.grab_set()
        for eachsong in self.game:
            self.get_all_buzzes()
            self.dosong(eachsong)
            #print(self.labellist[0].cget('text'))
            #self.labellist[0].config(text=self.labellist[0].cget('text'))
            self.update()
            time.sleep(3)
        maxscore = 0
        winner = []
        for contestant in range(3):
            if self.cont_exist[contestant]:
                if self.times[contestant] > 0:
                    newscore = round(self.scores[contestant] / self.times[contestant], 2)
                else:
                    newscore = 0
                self.labellist[contestant+4].config(text=str(newscore))
                if newscore > maxscore:
                    maxscore = newscore
                    winner = [contestant]
                elif newscore == maxscore:
                    winner.append(contestant)
        if len(winner) == 0:
            self.mainlabeltext.set('Nobody wins')
        elif len(winner) == 1:
            self.mainlabeltext.set(self.labellist[winner[0]+1].cget('text') + ' wins!')
        elif len(winner) == 2:
            self.mainlabeltext.set(self.labellist[winner[0]+1].cget('text') + ' & ' + self.labellist[winner[1]+1].cget('text') + ' tie!')
        elif len(winner) == 3:
            self.mainlabeltext.set('Everyone ties!')
        self.update()

class GameSettingsWindow(tk.Toplevel): # Allows the player(s) to choose how strictly
    def __init__(self):                # the game operates and how many contestants
        tk.Toplevel.__init__(self)     # play, via radio buttons, and returns them
        self.title("Game options")     # with the bearfruit method when the 'PLAY'
        self.resizable(False,False)    # button on the window is selected.
        self.iconbitmap('.\Music\KathySong.ico')
        self.config(bg='yellow')
        ACCEPTANCES = ['strict','inclusive','loose']
        CONTESTANTS = ['single','dual','triple']
        self.ACCEPTANCE = tk.StringVar()
        self.CONTESTANT = tk.StringVar()
        tk.Label(self,text='Answer acceptability:',bg='yellow',font=PLAY_MENU_FONT).grid(column=0,row=0,padx=5,pady=5)
        tk.Label(self,text='Contestant mode:',bg='yellow',font=PLAY_MENU_FONT).grid(column=1,row=0,padx=5,pady=5)
        for acceptanceoption in ACCEPTANCES:
            r = tk.Radiobutton(self,text=acceptanceoption,bg='yellow',font=PLAY_MENU_FONT,value=acceptanceoption,variable=self.ACCEPTANCE)
            r.grid(column=0,row=ACCEPTANCES.index(acceptanceoption)+1)
        for contestantoption in CONTESTANTS:
            r = tk.Radiobutton(self,text=contestantoption,bg='yellow',font=PLAY_MENU_FONT,value=contestantoption,variable=self.CONTESTANT)
            r.grid(column=1,row=CONTESTANTS.index(contestantoption)+1)
        self.submitted = tk.BooleanVar()
        def submit():
            self.submitted.set(True)
        tk.Button(self,text="PLAY!",bg=BUTTONBACKGROUNDCOLOR,fg=BUTTONTEXTCOLOR,font=MAIN_PLAY_FONT,command=submit).grid(column=0,row=4,columnspan=2)
        self.protocol('WM_DELETE_WINDOW',self.on_exit)

    def bearfruit(self):
        self.wait_variable(self.submitted)
        return self.ACCEPTANCE.get(), self.CONTESTANT.get()

    def on_exit(self): # In play, this window is made, bearfruit called, and
        self.ACCEPTANCE.set(None) # destroyed externally soon after, allowing this.
        self.submitted.set(True) # None will cause the play not to run, the presumed
                                    # goal of choosing 'x' and not play.
class SongEditWindow(tk.Toplevel):
    def __init__(self,master,songfile):
        tk.Toplevel.__init__(self,master)
        self.title("Add song")
        self.resizable(False,False)
        self.iconbitmap('.\Music\KathySong.ico')
        if isinstance(songfile,Song):
            self.songfile = songfile.fileloc
            self.needletime = songfile.start
        else:
            self.songfile = songfile
            self.needletime = 0.000
        tk.Label(self,text="Title:  ").grid(column=0, columnspan=4, row=0, padx=5, pady=5)
        tk.Label(self,text="Artist:  ").grid(column=0, columnspan=4, row=1, padx=5, pady=5)
        tk.Label(self,text="Hint:  ").grid(column=0, columnspan=4, row=2, padx=5, pady=5)
        title_ent = ttk.Entry(self)
        title_ent.grid(column=5, columnspan=4, row=0, padx=5, pady=5)
        artist_ent = ttk.Entry(self)
        artist_ent.grid(column=5, columnspan=4, row=1, padx=5, pady=5)
        hint_ent = ttk.Entry(self)
        hint_ent.grid(column=5, columnspan=4, row=2, padx=5, pady=5)
        if isinstance(songfile,Song):
            title_ent.insert(0,songfile.titles[-1])
            artist_ent.insert(0,songfile.artist)
            hint_ent.insert(0,songfile.hint)
        else:
            title_ent.insert(0,songfile.split('/')[-1][:-4])

        tk.Label(self,text="Skip by:  ").grid(column=9, row=1, padx=5, pady=5)
        tk.Label(self,text="Excerpt length:  ").grid(column=9, row=2, padx=5, pady=5)
        self.SKIP_LENGTHS = {'1/10 sec':100,'1 sec':1000,'5 sec':5000}
        self.EXCERPT_LENGTHS = {'1/2 sec':500,'1 sec':1000,'2 sec':2000,'3 sec':3000,'6 sec':6000,'15 sec':15000}
        skip_cbox = ttk.Combobox(self,values = list(self.SKIP_LENGTHS))
        skip_cbox.set('5 sec')
        skip_cbox.grid(column=10, row=1, padx=5, pady=5)
        exc_cbox = ttk.Combobox(self,values = list(self.EXCERPT_LENGTHS))
        if isinstance(songfile,Song) and songfile.duration != 500:
            exc_cbox.set(str(int(songfile.duration/1000))+' sec')
        else:
            exc_cbox.set('1/2 sec')
        exc_cbox.grid(column=10, row=2, padx=5, pady=5)
        time_pbar = ttk.Progressbar(self)
        time_pbar.grid(column=5,row=3,columnspan=6,padx=5,pady=5,sticky=tk.EW)
        self.boxes = [title_ent,artist_ent,hint_ent,skip_cbox,exc_cbox,time_pbar]
        self.starttime = 0.000
        self.stoptime = 0.000

        #try:
        #    if self.songfile[-1] == '3':
        #        self.whole_song_as = AudioSegment.from_mp3(self.songfile)
        #    else:
        #        self.whole_song_as = AudioSegment.from_wave_file(self.songfile)
        #    self.song_length = len(self.whole_song_as)
        #except:
        #    tk.messagebox.showerror("Error",f"Pydub cannot load file {self.songfile}.\nTry editing the file's metadata and moving it.")
        #    self.boxes[0].insert(0,"⛔")

        if self.songfile[-1] == '3':
            self.whole_song_as = AudioSegment.from_mp3(self.songfile)
        else:
            self.whole_song_as = AudioSegment.from_wave_file(self.songfile)
        self.song_length = len(self.whole_song_as)

        tk.Button(self,text=" ▶️",command=lambda:  self.play_song(),width=2).grid(column=2,row=3,pady=5)
        tk.Button(self,text='⏸️',command=lambda:  self.pause_song()).grid(column=1,row=3,pady=5)
        tk.Button(self,text="⏪",command=lambda:  self.back_five()).grid(column=0,row=3,pady=5)
        tk.Button(self,text="⏩",command=lambda:  self.bump_five()).grid(column=3,row=3,pady=5)
        tk.Button(self,text="🎧",command=lambda:  self.excerpt_song()).grid(column=4,row=3,pady=5)
        tk.Button(self,text="Add song",command=lambda:  self.assemble_song()).grid(column=10, row=0, padx=5, pady=5)
        self.done = tk.BooleanVar(value=False)

    def skip_length(self):
        return self.SKIP_LENGTHS[self.boxes[3].get()]

    def excerpt_length(self):
        return self.EXCERPT_LENGTHS[self.boxes[4].get()]

    def play_song(self):
        sa.stop_all()
        self.whole_song_as[self.needletime:].export("temp.wav",format="wav")
        self.song_playing = sa.WaveObject.from_wave_file("temp.wav")
        self.starttime = time.time()
        self.song_playing.play()

    def pause_song(self):
        sa.stop_all()
        self.stoptime = time.time()
        self.needletime += 1000*(self.stoptime - self.starttime)
        self.boxes[5]['value']= 100*self.needletime/self.song_length

    def back_five(self):
        sa.stop_all()
        self.needletime -= self.skip_length()
        if self.needletime < 0:
            self.needletime = 0
        self.boxes[5]['value'] = 100*self.needletime/self.song_length

    def bump_five(self):
        sa.stop_all()
        self.needletime += self.skip_length()
        if self.needletime > self.song_length - self.excerpt_length():
            self.needletime = self.song_length - self.excerpt_length()
        self.boxes[5]['value'] = 100*self.needletime/self.song_length

    def excerpt_song(self):
        sa.stop_all()
        play(self.whole_song_as[self.needletime:self.needletime+self.excerpt_length()])

    def assemble_song(self):
        sa.stop_all()
        self.done.set(True)

    def bearfruit(self):
        if self.boxes[0].get()[0] != "⛔":
            self.wait_variable(self.done)
            if self.done.get():
                return Song([self.boxes[0].get()],self.boxes[1].get(),self.boxes[2].get(),self.songfile,self.needletime,self.excerpt_length())
            return "⛔" # When this string is sent in lieu of a song, nothing is
        else: # appended to the game.  This occurs when a file is not found, or
            return "⛔" # when the 'x' button is selected.

    def on_exit(self):
        self.done.set(False)

#class RemoveSongWindow(tk.Toplevel):
#    def __init__(self,master):
#        tk.Toplevel.__init__(self,master)
#        self.title("Remove song")
#        self.resizable(True,True)
#        self.iconbitmap('.\Music\KathySong.ico')
#        self.titlelist = []
#        for eachsong in master.game:
#            self.titlelist.append(eachsong[1])
#        tk.Label(self,text="Song:").grid(column=0,row=0)
#        sng_cbox = ttk.Combobox(self,state="readonly",value=self.titlelist)
#        sng_cbox.grid(column=1,columnspan=2, row=0)
#
#        def remove_song():
#            self.titlelist.remove(sng_cbox.get())
#            titletext = ''
#            for eachsong in self.titlelist:
#                titletext += eachsong + '\n'
#            ind = sng_cbox.current()
#            master.game.remove(game[ind])
#            master.labels[0].config(text="Songs:  "+str(len(self.titlelist)))
#            master.labels[1].config(text=titletext)
#            self.destroy()
#        tk.Button(self,text="Remove selected song",command=lambda: remove_song()).grid(column=0,row=1,padx=5,pady=5)
#        tk.Button(self,text="Cancel",command=lambda:  self.destroy()).grid(column=2,row=1,padx=5,pady=5)

class GameEditWindow(tk.Toplevel): # Allows for the editing of a game (as a list
    def __init__(self,master):     # of song objects).
        tk.Toplevel.__init__(self,master)
        self.title("KathySong game editor")
        self.resizable(True,False)
        self.iconbitmap('.\Music\KathySong.ico')
        self.game = []

        self.columnconfigure([0,1,3],weight=0)
        self.columnconfigure(2,weight=1)

        tk.Label(self,text="Game title:").grid(column=0, row=0, columnspan=2, sticky=tk.W)
        self.title_box = ttk.Entry(self)
        day = datetime.datetime.now().weekday()
        if day == 6:
            self.title_box.insert(0, "Another pleasant valley Sunday") # I had to put a quoted string right in the argument -
        elif day == 0:                                            # Anything else threw a strange error
            self.title_box.insert(0, "Just another manic Monday")
        elif day == 1:
            self.title_box.insert(0, "Tuesday's gone with the wind")
        elif day == 2:
            self.title_box.insert(0, "Listen to Wednesday's song")
        elif day == 3:
            self.title_box.insert(0, "I am Thursday's child")
        elif day == 4:
            self.title_box.insert(0, "It's Friday, I'm in love")
        elif day == 5: # The music video for Rebecca Black's "Friday" didn't include a page for Saturday 🤷
            self.title_box.insert(0, "Saturday night's alright for fighting")
        self.title_box.grid(column=2, columnspan=2, row=0, padx=5, pady=5, sticky=tk.EW)

        numsongs_label = tk.Label(self,text="Songs:  0")
        numsongs_label.grid(column=0, row=1, columnspan=2,sticky=tk.W, padx=5, pady=5)
        self.active_directory = '/'
        scroller = ttk.Scrollbar(self)
        scroller.grid(column=3,row=1,rowspan=9,sticky=tk.NS)
        song_list = tk.Listbox(self,width=30,yscrollcommand=scroller.set,selectmode=tk.MULTIPLE)
        song_list.grid(column=2,row=1,rowspan=9,padx=5,pady=5,sticky=tk.NS +tk.EW)
        scroller.config(command=song_list.yview)
        self.labels = [numsongs_label,song_list]

        tk.Button(self,text="Add song",command=lambda:  self.add_song()).grid(column=0,row=2, columnspan=2,padx=5, pady=5)
        tk.Button(self,text="🔝",width=2,command=lambda:  self.first_song()).grid(column=0,row=3,padx=5,pady=5)
        tk.Button(self,text=" ⬆️",width=2,command=lambda:  self.raise_song()).grid(column=1,row=3,padx=5,pady=5)
        tk.Button(self,text=" ⬇️",width=2,command=lambda:  self.lower_song()).grid(column=0,row=4,padx=5,pady=5)
        tk.Button(self,text="🔀",width=2,command=lambda:  self.shuffle_songs()).grid(column=1,row=4,padx=5,pady=5)
        tk.Button(self,text="Edit sample",command=lambda:  self.edit_song()).grid(column=0,row=5,columnspan=2,padx=5,pady=5)
        tk.Button(self,text="Remove song",command=lambda:  self.remove_song()).grid(column=0,row=6,columnspan=2,padx=5,pady=5)
        tk.Button(self,text="Load game",command=lambda:  self.loadgame()).grid(column=0,row=7,columnspan=2,padx=5,pady=5)
        tk.Button(self,text="Save game",command=lambda:  self.save()).grid(column=0,row=8,columnspan=2,padx=5,pady=5)
        tk.Button(self,text="Main menu",command=lambda:  self.exit()).grid(column=0,row=9,columnspan=2,padx=5,pady=5)

    def update_list(self): # Changes the list of songs to reflect the self.game.
        self.labels[0].config(text="Songs:  "+str(len(self.game)))
        self.labels[1].delete(0,tk.END)
        for eachsong in self.game:
            self.labels[1].insert(tk.END,eachsong.titles[0])

    def add_song(self):
        possiblesong = filedialog.askopenfilename(initialdir = self.active_directory,title='Select song', filetypes = (('MP3 Files','*.mp3*'),('WAV Files','*.wav*')))
        if possiblesong != '':
            addsongwindow = SongEditWindow(self,possiblesong)
            newsong = addsongwindow.bearfruit()
            if newsong != "⛔":
                self.game.append(newsong)
                self.update_list()
                self.active_directory = '/'.join(self.game[-1].fileloc.split('/')[:-1])
            addsongwindow.destroy()
            self.grab_set()

    def first_song(self):
        choice = self.labels[1].curselection()
        newgame = []
        for eachsong in choice:
            newgame.append(self.game.pop(eachsong))
        newgame.extend(self.game)
        self.game = newgame
        self.update_list()

    def raise_song(self):
        choice = self.labels[1].curselection()
        for eachsong in choice:
            if eachsong != 0:
                self.game.insert(eachsong-1,self.game.pop(eachsong))
        self.update_list()

    def lower_song(self):
        choice = self.labels[1].curselection()
        for eachsong in choice:
            if eachsong != len(self.game) - 1:
                self.game.insert(eachsong,self.game.pop(eachsong+1))
        self.update_list()

    def shuffle_songs(self):
        random.shuffle(self.game)
        self.update_list()

    def edit_song(self):
        choice = self.labels[1].curselection()
        if len(choice) == 1:
            addsongwindow = SongEditWindow(self,self.game[choice[0]])
            self.game[choice[0]] = addsongwindow.bearfruit()
            self.update_list()
            addsongwindow.destroy()
            self.grab_set()
        else:
            tk.messagebox.showerror("Select one song to edit.")

    def remove_song(self):
        choice = self.labels[1].curselection()
        changes = 0
        for eachsong in choice:
            if tk.messagebox.askquestion("Remove?",f'Remove "{self.game[eachsong-changes].titles[0]}"?') == 'yes':
                self.game.pop(eachsong-changes)
                changes += 1
        self.update_list()

    def loadgame(self):
        if self.game != []:
            ch = tk.messagebox.askquestion("Extend this game?","Extend this game?")
        else:
            ch = 'yes'
        if ch == 'no':
            return None # Consider cool feature like appending game
        chosenfile = filedialog.askopenfilename(initialdir='./Saved Games',title='Select gamefile')
        if chosenfile == '': # If the user chooses "cancel" in explorer
            return None
        if self.game == []:
            self.title_box.delete(0, tk.END)
            self.title_box.insert(0, chosenfile.split("/")[-1][:-4])
        with open(chosenfile,'r') as chosenfile:
            song = []
            line = 0
            for eachline in chosenfile.readlines():
                song.append(eachline[:-1])
                line += 1
                if line % 6 == 0:
                    self.game.append(Song(song[1].split("|"),song[2],song[3],song[0],float(song[4]),int(song[5])))
                    song = []
        for eachsong in self.game:
            if not os.path.isfile(eachsong.fileloc):
                messagebox.showerror('Error',f'Could not locate file:  {eachsong}')
                return None
        self.update_list()
        self.grab_set()
        self.master.lower()

    def save(self): # Games are always saved to the Saved Games folder.
        game_name = self.title_box.get()
        checkfile = './Saved Games/'+game_name+'.txt'
        trie = 0
        while os.path.isfile(checkfile):
            trie += 1
            checkfile = './Saved Games/'+game_name+' ('+str(trie)+').txt'
        with open(checkfile,'w') as gamefile:
            for eachsong in self.game:
                gamefile.write(eachsong.get_writeable())
                gamefile.write('\n')
        messagebox.showinfo('information','Game saved as '+checkfile.split('/')[-1])
        self.master.deiconify()
        self.destroy()

    def exit(self):
        if tk.messagebox.askquestion("Exit without saving?","Exit without saving?") == 'yes':
            self.master.deiconify()
            self.destroy()

class MainMenuWindow(tk.Tk): # The main menu has three methods:  one for loading
    def __init__(self):      # a game, used by the playing method upon hitting
        tk.Tk.__init__(self) # 'play', and one for opening the game-making window.
        self.title("KathySong")
        self.resizable(False,False)
        swid, shei = self.winfo_screenwidth()-40, self.winfo_screenheight() - 120
        self.geometry(f"{swid}x{shei}+20+45")
        self.iconbitmap('.\Music\KathySong.ico')
        self.configure(bg='yellow')

        MAINMENUFONT = font.Font(family='Segoe Print', size=40)

        self.columnconfigure([0,2],weight=1)
        self.columnconfigure(1,weight=2)
        self.rowconfigure([0,1],weight=2)
        self.rowconfigure(2,weight=1)
        tk.Button(self, text="Play game", font=MAINMENUFONT, bg=BUTTONBACKGROUNDCOLOR, fg=BUTTONTEXTCOLOR, command=lambda: self.playgame()).grid(column=1, row=0)
        tk.Button(self, text="Compose game", font=MAINMENUFONT, bg=BUTTONBACKGROUNDCOLOR, fg=BUTTONTEXTCOLOR, command=lambda: self.composegame()).grid(column=1, row=1)
        tk.Button(self, text="Quit", font=MAINMENUFONT, bg=BUTTONBACKGROUNDCOLOR, fg=BUTTONTEXTCOLOR, command=lambda: self.destroy()).grid(column=2, row=2)

    def loadgame(self):
        chosenfile = filedialog.askopenfilename(initialdir='./Saved Games',title='Select gamefile')
        if chosenfile == '': # If the user chooses "cancel" in explorer
            return None
        with open(chosenfile,'r') as chosenfile:
            game = []
            song = []
            line = 0
            for eachline in chosenfile.readlines():
                song.append(eachline[:-1])
                line += 1
                if line % 6 == 0:
                    game.append(Song(song[1].split("|"),song[2],song[3],song[0],float(song[4]),int(song[5])))
                    song = []
        for eachsong in game:
            if not os.path.isfile(eachsong.fileloc):
                messagebox.showerror('Error',f'Could not locate file:  {eachsong}')
                return None
        return game

    def playgame(self):
        game = self.loadgame()
        if game: # Yields False when loadgame yields None, which is when the user chose not to load a game in Explorer.
            self.withdraw()
            gsw = GameSettingsWindow()
            ACCEPTANCE, CONTESTANT = gsw.bearfruit()
            print(f"Acceptance: {ACCEPTANCE}")
            gsw.destroy()
            if ACCEPTANCE in ['strict','inclusive','loose']:
                self.wait_window(PlayWindow(self,ACCEPTANCE,CONTESTANT,game).run_game())
            self.deiconify()
            self.grab_set()

    def composegame(self):
        self.withdraw()
        self.wait_window(GameEditWindow(self))
        self.deiconify()
        self.grab_set()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = MainMenuWindow() # Placing fonts before the root was declared caused error.
    PLAYER_NAME_FONT = font.Font(family="Segoe Print",size=60,weight='bold')
    PLAYER_SCORE_FONT = font.Font(family="Helvetica",size=36)
    MAIN_PLAY_FONT = font.Font(family="Helvetica",size=48)
    PLAY_MENU_FONT = font.Font(family="Segoe Print",size=24)
    EDIT_MENU_FONT = font.Font(family="MS Sans Serif",size=24)
    DEFAULT_FONT = font.nametofont("TkDefaultFont")
    DEFAULT_FONT.config(size=16)
    TEXT_FONT = font.nametofont("TkTextFont")
    TEXT_FONT.config(size=16)
    root.mainloop()
