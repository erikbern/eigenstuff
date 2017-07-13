import bs4, itertools, json, matplotlib, numpy, os, random, re, requests, sys, time
from matplotlib import pyplot

cache = {}
if os.path.exists('cache.tsv'):
    for line in open('cache.tsv'):
        q, n = line.strip().split('\t')
        cache[q] = int(n)

def get_n_results_dumb(q):
    r = requests.get('http://www.google.com/search',
                     params={'q': q,
                             "tbs": "li:1"})
    r.raise_for_status()
    soup = bs4.BeautifulSoup(r.text)
    s = soup.find('div', {'id': 'resultStats'}).text
    if not s:
        return 0
    m = re.search(r'([0-9,]+)', s)
    return int(m.groups()[0].replace(',', ''))

data = json.load(open(sys.argv[1]))
tag = data['tag']
items = data['items']
verbs = data['verbs']

item2i = dict([(item, i) for i, item in enumerate(items)])

qs = []
for item1, item2 in itertools.product(items, items):
    if item1 != item2:
        for verb in verbs:
            qs.append((item2i[item1], item2i[item2], '"%s from %s to %s"' % (verb, item1, item2)))
            qs.append((item2i[item1], item2i[item2], '"%s to %s from %s"' % (verb, item2, item1)))

m = numpy.zeros((len(items), len(items)))
random.shuffle(qs)
print(100. * len(set(cache).intersection([q for _, _, q in qs])) / len(qs))

for i, j, q in qs:
    if q in cache:
        n = cache[q]
    else:
        sys.stdout.write('%50s...' % q)
        sys.stdout.flush()
        n = get_n_results_dumb(q)
        sys.stdout.write('%9d\n' % n)
        f = open('cache.tsv', 'a')
        f.write('%s\t%d\n' % (q, n))
        f.close()
    m[j][i] += n

def plot_mat(m, items, cm, fn, fmt, dir_text=None):
    s = 4 + len(items) * 0.3
    fig = pyplot.figure(figsize=(s, s))
    ax = fig.add_subplot(111)
    ax.xaxis.set_label_position('top')
    ax.matshow(m.T + 1, cmap=cm, norm=matplotlib.colors.LogNorm(vmin=numpy.min(m+1), vmax=numpy.max(m+1)))

    if dir_text:
        ax.set_xlabel('To language\n< Smaller %s %10s Larger %s >' % (dir_text, '', dir_text))
        ax.set_ylabel('From language\n< Larger %s %10s Smaller %s >' % (dir_text, '', dir_text))
    else:
        ax.set_xlabel('To language')
        ax.set_ylabel('From language')
    ax.set_xticks(numpy.arange(0, len(items)))
    ax.set_yticks(numpy.arange(0, len(items)))
    ax.set_xticklabels(items, rotation=90, ha='center')
    ax.set_yticklabels(items, va='center')
    ax.set_xticks(numpy.arange(0.5, len(items)+0.5), minor=True)
    ax.set_yticks(numpy.arange(0.5, len(items)+0.5), minor=True)
    ax.grid(which='minor')

    for i in range(len(items)):
        for j in range(len(items)):
            text = fmt % m[i][j]
            if text != fmt % 0:
                ax.text(i, j, text, va='center', ha='center', size=7)

    fig.tight_layout()
    pyplot.savefig(fn, dpi=300)

# Plot lexicographical
ps = sorted(range(len(items)), key=lambda i: items[i])
plot_mat(m[ps,:][:,ps], sorted(items), pyplot.cm.OrRd, '%s_matrix.png' % tag, '%.0f')

# m += numpy.eye(len(items)) # hack to fix zero entries
for item, pop in zip(items, m.sum(axis=0) + m.sum(axis=1)):
    print('%20s %6d' % (item, pop))
m /= m.sum(axis=0)[numpy.newaxis,:]
u = numpy.ones(len(items))

for i in range(100):
    u = numpy.dot(m, u)
    u /= u.sum()

# Create a new matrix where rows/columns are ordered by u
ps = sorted(range(len(items)), key=lambda i: u[i])
for p in reversed(ps):
    print('| %5.2f%% | %20s |' % (u[p]*100, items[p]))

m_new = m[ps,:][:,ps]
plot_mat(m_new, [items[p] for p in ps], pyplot.cm.BuGn, '%s_matrix_eig.png' % tag, '%.2f', dir_text='future popularity')
