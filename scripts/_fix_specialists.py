content = open('D:/project/HACKATHONAI/models/experts/specialists.py', 'r', encoding='utf-8').read()
old = '"n_features": self.classifier.n_features_in_},'
new = '"n_features": getattr(self.classifier.model, "n_features_in_", 8)},'
content2 = content.replace(old, new, 1)
if content2 == content:
    print('NO CHANGE - pattern not found')
else:
    open('D:/project/HACKATHONAI/models/experts/specialists.py', 'w', encoding='utf-8').write(content2)
    print('REPLACED OK')

