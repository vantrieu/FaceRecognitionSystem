from tkinter import * 
from tkinter.ttk import *
import tkinter.messagebox as mbox
import cv2
import numpy as np
import pyodbc
import os
from PIL import Image
import time


class MainForm(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.sv = StringVar()
        self.initUI()

    def initUI(self):
        self.parent.title("Face Recognition System")
        self.pack(fill=BOTH, expand=True)

        frame = Frame(self)
        frame.pack(fill=X)

        lbl1 = Label(frame, text="Hello! Can i help you?")
        lbl1.configure(font=("Times New Roman", 16, "bold"), anchor="center")
        lbl1.pack(fill=BOTH)
    
        frame1 = Frame(self)
        frame1.pack(fill=X)
        
        btnAddPeople = Button(frame1, text="Add identification data", width=25, command=self.addPeople)
        btnAddPeople.pack()

        btnTrainData = Button(frame1, text="Identification data training", width=25, command=self.trainData)
        btnTrainData.pack()

        btnIdentif = Button(frame1, text="Face recognition", width=25, command=self.faceRecognition)
        btnIdentif.pack()

    # def callback(sv):
    #     print(sv.get())

    def addPeople(self):
        frmGetData = Toplevel(self)
        frmGetData.geometry("376x130+540+300")
        frmGetData.title("Get Identification Data")
    
        lbl1 = Label(frmGetData, text="Enter people name", width=6)
        lbl1.pack(fill=X, padx=5)
    
        entry1 = Entry(frmGetData, textvariable=self.sv)
        entry1.pack(fill=X, padx=5)

        btnAdd = Button(frmGetData, text="Save", command = self.saveData)
        btnAdd.pack()
    
    def saveData(self):
        conn = pyodbc.connect('Driver={SQL Server};'
                          'Server=.;'
                          'Database=data;'
                          'Trusted_Connection=yes;')
        query = "SELECT * FROM people WHERE Name = '" + str(self.sv.get()) + "'"
        cursor = conn.execute(query)
        isRecordExist = 0
        for row in cursor:
            isRecordExist = 1
        if(isRecordExist == 0):
            query = "INSERT INTO people(Name) OUTPUT Inserted.ID VALUES(" + "'" + str(self.sv.get()) + "')"
        cursor = conn.execute(query)
        id = cursor.fetchone()[0]
        conn.commit()        
        conn.close()
        face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        cap = cv2.VideoCapture(0)
        sampleNum = 0
        while(True):
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for(x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 225, 0), 2)
                if not os.path.exists('dataSet'):
                    os.makedirs('dataSet')
                sampleNum += 1
                cv2.imwrite('dataSet/User.'+ str(id) + '.' + str(sampleNum) + '.jpg', gray[y: y + h, x: x + w])
            cv2.imshow('frame', frame)
            time.sleep(0.3)
            cv2.waitKey(1)            
            if(sampleNum > 100):
                break
        cap.release()
        cv2.destroyAllWindows()
        python = sys.executable
        os.execl(python, python, * sys.argv)
    
    def trainData(self):
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        path = 'dataSet'
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]    
        faces = []
        Ids = []
        for imagePath in imagePaths:
            faceImg = Image.open(imagePath).convert('L')
            faceNp = np.array(faceImg, 'uint8')
            Id = int(imagePath.split('\\')[1].split('.')[1])            
            faces.append(faceNp)
            Ids.append(Id)
            cv2.imshow('Trainning Data', faceNp)
            cv2.waitKey(20)
        recognizer.train(faces, np.array(Ids))
        if not os.path.exists('recognizer'):
            os.makedirs('recognizer')
        recognizer.save('recognizer/trainningData.yml')
        cv2.destroyAllWindows()
        mbox.showinfo("Successfully", "Completed train data!")

    def faceRecognition(self):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('recognizer/trainningData.yml')
        cap = cv2.VideoCapture(0)
        fontface = cv2.FONT_HERSHEY_SIMPLEX
        while(True):
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray)
            for(x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,225,0), 2)
                roi_gray = gray[y: y+ h, x: x+ h]
                id, confidence = recognizer.predict(roi_gray)
                if confidence < 40:
                    conn = pyodbc.connect('Driver={SQL Server};'
                          'Server=.;'
                          'Database=data;'
                          'Trusted_Connection=yes;')
                    query = "SELECT * FROM people WHERE ID=" + str(id)
                    cursor = conn.execute(query)
                    profile = None
                    for row in cursor:
                        profile = row
                    conn.close()
                    if profile != None:
                        cv2.putText(frame, "" + str(profile[1]) + " " + str(100 - confidence) + "%", (x+10, y+h+30), fontface, 1, (0,255,0), 2)
                    else:
                        cv2.putText(frame, "Unknow", (x+10, y+h+30), fontface, 1, (0, 0, 255), 2)
            cv2.imshow('Detect',frame)
            if(cv2.waitKey(1) & 0xFF == ord('q')):
                break
        cap.release()
        cv2.destroyAllWindows()

root = Tk()
root.geometry("376x130+540+300")
app = MainForm(root)
root.mainloop()
