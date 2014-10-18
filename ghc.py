#!/usr/bin/env python3

import sys
import os
from paths import app_folder
from qsettings import QSettings
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QMessageBox, QInputDialog, QFileDialog
from PyQt5.QtWebKitWidgets import QWebView

settings = QSettings(dirname="githost-client")

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.webView = QWebView(self)
        self.webView.settings().setAttribute(self.webView.settings().globalSettings().DeveloperExtrasEnabled, True)
        self.webView.settings().setUserStyleSheetUrl(QUrl.fromUserInput(os.path.join(app_folder, "style.css")))
        self.webView.loadFinished.connect(self.jsHack)
        self.setCentralWidget(self.webView)
        
        # Main toolbar
        self.toolBar = QToolBar(self)
        self.toolBar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.addToolBar(self.toolBar)
        
        page = self.webView.page()

        backAction = page.action(page.Back)
        backAction.setShortcut("Alt+Left")
        self.toolBar.addAction(backAction)
        
        nextAction = page.action(page.Forward)
        nextAction.setShortcut("Alt+Right")
        self.toolBar.addAction(nextAction)
        
        reloadAction = page.action(page.Reload)
        reloadAction.setShortcuts(["Ctrl+R", "F5"])
        self.toolBar.addAction(reloadAction)
        
        stopAction = page.action(page.Stop)
        stopAction.setShortcut("Esc")
        self.toolBar.addAction(stopAction)
        
        self.toolBar.addSeparator()

        style = QApplication.style()

        self.uploadAction = QAction(self, text="Upload", icon=style.standardIcon(style.SP_ArrowUp))
        self.uploadAction.setShortcut("Alt+Up")
        self.uploadAction.triggered.connect(self.upload)
        self.toolBar.addAction(self.uploadAction)

        self.setGitHubSiteAction = QAction(self, text="Set Page", icon=style.standardIcon(style.SP_FileIcon))
        self.setGitHubSiteAction.setShortcut("Ctrl+L")
        self.setGitHubSiteAction.triggered.connect(self.setGitHubSite)
        self.toolBar.addAction(self.setGitHubSiteAction)

        self.setGitDirectoryAction = QAction(self, text="Set Directory", icon=style.standardIcon(style.SP_DirIcon))
        self.setGitDirectoryAction.setShortcut("Ctrl+O")
        self.setGitDirectoryAction.triggered.connect(self.setGitDirectory)
        self.toolBar.addAction(self.setGitDirectoryAction)
        
        self.webView.load(QUrl.fromUserInput(settings.value("settings/GitUrl")))

    def setGitHubSite(self):
        url = QInputDialog.getText(self, "Githost", "Enter your site here:")
        if url[1]:
            settings.setValue("settings/GitUrl", url[0])
            self.webView.load(QUrl.fromUserInput(settings.value("settings/GitUrl")))
            settings.sync()

    def setGitDirectory(self):
        gitRepo = QFileDialog.getExistingDirectory(self, "Select directory...", os.path.expanduser("~"))
        if not os.path.isdir(gitRepo):
            pass
        else:
            settings.setValue("settings/GitRepo", gitRepo)
            settings.sync()

    def upload(self):
        if not settings.value("settings/GitRepo"):
            QMessageBox.information(self, "Githost", "Please select the directory of your Git repository.")
            self.setGitDirectory()
        repo = settings.value("settings/GitRepo")
        if repo:
            fnames = QFileDialog.getOpenFileNames(self, "Select files to upload...", os.path.expanduser("~"), "All files (*)")
            if type(fnames) is tuple:
                fnames = fnames[0]
            if not settings.value("settings/NoPromptForGitRepo") and len(fnames) > 0:
                confirm = QMessageBox.question(self, "Confirm selection", "Commit files to repository?", QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.No)
            else:
                confirm = QMessageBox.Yes
            if confirm == QMessageBox.YesToAll:
                settings.setValue("settings/NoPromptForGitRepo", True)
            if len(fnames) > 0 and confirm in (QMessageBox.Yes, QMessageBox.YesToAll):
                for fname in fnames:
                    os.system("cp %s %s" % (fname, repo))
                os.system("cd %s && git add . && git commit -m \"Added %s new file%s.\"" % (repo, len(fnames), ("s" if len(fnames) > 1 else "")))
                os.system("cd %s && xterm -e \"git push --all\" &" % (repo,))

    def jsHack(self):
        self.webView.page().mainFrame().evaluateJavaScript("""contents = document.getElementsByClassName("content");
        links = document.getElementsByClassName("js-directory-link");
        for(i=0; i<contents.length;i++) {
            br = document.createElement("br");
            contents[i].appendChild(br);
            imgLink = document.location.href.replace("github.com", "raw.githubusercontent.com") + "/master/" + links[i].innerHTML;
            /*links[i].innerHTML = "";
            img = document.createElement("img");
            img.src = imgLink;
            img.setAttribute("style", "height: 128px;");
            links[i].appendChild(img);*/
            input = document.createElement("input");
            input.setAttribute("style", "width: 100%;");
            input.setAttribute("value", "[IMG]" + imgLink + "[/IMG]");
            contents[i].appendChild(input);
        }""")

def main(argv):
    app = QApplication(argv)
    app.setApplicationName("Githost")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main(sys.argv)
