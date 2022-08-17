from gc__listoffers.application import Application

app = Application()
app.mainloop()
app.localConnectionProcess.terminate()
