from gc__listoffers.application import Application
import multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = Application()
    app.mainloop()
    app.localConnectionProcess.terminate()
