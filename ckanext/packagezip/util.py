from itertools  import count

class FilenameDeduplicator(object):
    def __init__(self):
        self.reset()

    def  reset(self):
        self.seen = []

    def deduplicate(self, filename):
        if filename in self.seen:
            parts = filename.rsplit('.', 1)
            for i in count(1):
                if len(parts) == 2:
                    filename = u"{0}{1}.{2}".format(parts[0], i, parts[1])
                else:
                    filename = u"{0}{1}".format(parts[0], i)

                if filename not in self.seen:
                    break

        self.seen.append(filename)
        return filename
