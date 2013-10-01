from spambayes.classifier import Classifier
from spambayes.hammie import Hammie

from .models import Session, BayesWord

class AlchemyClassifier(Classifier):
    def __init__(self, model):
        Classifier.__init__(self)
        self.model = model
        self.statekey = ''
        self.nspam = 0
        self.nham = 0
        self.load()

    def _set_row(self, word, nspam, nham):
        data = {
            'word': word,
            'nspam': nspam,
            'nham': nham
        }
        word, created = self.model.get_or_create(word, data)
        Session.commit()

    def load(self):
        word = self.model.get(self.statekey)
        self.nspam = word.nspam if word else 0
        self.nham = word.nham if word else 0

    def store(self):
        self._set_row(self.statekey, self.nspam, self.nham)

    def _wordinfoget(self, w):
        item = self.WordInfoClass()

        word = self.model.get(w)
        if word:
            item.__setstate__((word.nspam, word.nham))
      
        return item

    def _wordinfoset(self, word, item):
        self._set_row(word, item.spamcount, item.hamcount)

    def _wordinfodel(self, w):
        word = self.model.get(w)
        if not word:
            return 

        Session.delete(word)
        Session.commit()

    def _wordinfokeys(self):
        return [i.word for i in self.model.objects]

def train(path):

    db = AlchemyClassifier(BayesWord)
    db.load()
    spam_filter = Hammie(db, 'w')

    for name in os.listdir(path):
        print 'training %s...' % name

        try:
            message = email.message_from_file(open(os.path.join(path, name)))
            spam_filter.train(message, True)
            spam_filter.store()
        except Exception, e:
            Session.rollback()

