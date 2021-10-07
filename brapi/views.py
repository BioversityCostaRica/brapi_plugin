from climmob.plugins.utilities import climmobPublicView,climmobPrivateView

class myPublicView(climmobPublicView):
    def processView(self):
        return {}

class myPrivateView(climmobPrivateView):
    def processView(self):
        return {'activeUser': self.user}