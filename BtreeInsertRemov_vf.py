import bisect
import itertools
import operator

class _BNode(object):
    __slots__ = ["tree", "contents", "children"]

    def __init__(self, tree, contents=None, children=None):
        self.tree = tree
        self.contents = contents or []
        self.children = children or []
        if self.children:
            assert len(self.contents) + 1 == len(self.children), \
                    "one more child than data item required"

    def __repr__(self): #print para galhos ramos etc
        name = getattr(self, "children", 0) and "Branch" or "Leaf"
        return "<%s %s>" % (name, ", ".join(map(str, self.contents)))

    def lateral(self, parent, parent_index, dest, dest_index):
        if parent_index > dest_index:
            dest.contents.append(parent.contents[dest_index])
            parent.contents[dest_index] = self.contents.pop(0)
            if self.children:
                dest.children.append(self.children.pop(0))
        else:
            dest.contents.insert(0, parent.contents[parent_index])
            parent.contents[parent_index] = self.contents.pop()
            if self.children:
                dest.children.insert(0, self.children.pop())

    def shrink(self, ancestors):
        parent = None

        if ancestors:
            parent, parent_index = ancestors.pop()
            # tenta ir para o vizinho da esquerda/irmao
            if parent_index:
                left_sib = parent.children[parent_index - 1]
                if len(left_sib.contents) < self.tree.order:
                    self.lateral(
                            parent, parent_index, left_sib, parent_index - 1)
                    return

            # ttenta o vizinha da direita
            if parent_index + 1 < len(parent.children):
                right_sib = parent.children[parent_index + 1]
                if len(right_sib.contents) < self.tree.order:
                    self.lateral(
                            parent, parent_index, right_sib, parent_index + 1)
                    return

        center = len(self.contents) // 2
        sibling, push = self.split()

        if not parent:
            parent, parent_index = self.tree.BRANCH(
                    self.tree, children=[self]), 0
            self.tree._root = parent

        # passa o meio para vetor pai
        parent.contents.insert(parent_index, push)
        parent.children.insert(parent_index + 1, sibling)
        if len(parent.contents) > parent.tree.order:
            parent.shrink(ancestors)

    def grow(self, ancestors):
        parent, parent_index = ancestors.pop()

        minimum = self.tree.order // 2
        left_sib = right_sib = None

        # tenta emprestar do irmão da direita
        if parent_index + 1 < len(parent.children):
            right_sib = parent.children[parent_index + 1]
            if len(right_sib.contents) > minimum:
                right_sib.lateral(parent, parent_index + 1, self, parent_index)
                return

        # tenta emprestar do irmão da esquerda
        if parent_index:
            left_sib = parent.children[parent_index - 1]
            if len(left_sib.contents) > minimum:
                left_sib.lateral(parent, parent_index - 1, self, parent_index)
                return

        # junta com o irmão - tenta com o da esquerda primeiro
        if left_sib:
            left_sib.contents.append(parent.contents[parent_index - 1])
            left_sib.contents.extend(self.contents)
            if self.children:
                left_sib.children.extend(self.children)
            parent.contents.pop(parent_index - 1)
            parent.children.pop(parent_index)
        else:
            self.contents.append(parent.contents[parent_index])
            self.contents.extend(right_sib.contents)
            if self.children:
                self.children.extend(right_sib.children)
            parent.contents.pop(parent_index)
            parent.children.pop(parent_index + 1)

        if len(parent.contents) < minimum:
            if ancestors:
                # pai não é raiz
                parent.grow(ancestors)
            elif not parent.contents:
                # pai é raiz e agora é vazio
                self.tree._root = left_sib or self

    def split(self):
        center = len(self.contents) // 2
        median = self.contents[center]
        sibling = type(self)(
                self.tree,
                self.contents[center + 1:],
                self.children[center + 1:])
        self.contents = self.contents[:center]
        self.children = self.children[:center + 1]
        return sibling, median

    def insert(self, index, item, ancestors):
        self.contents.insert(index, item)
        if len(self.contents) > self.tree.order:
            self.shrink(ancestors)

    def remove(self, index, ancestors):
        minimum = self.tree.order // 2

        if self.children:
            # tenta subir da primeira subarvore da esquerda primeiro
            # só se não precisar mudar o tamanho
            additional_ancestors = [(self, index + 1)]
            descendent = self.children[index + 1]
            while descendent.children:
                additional_ancestors.append((descendent, 0))
                descendent = descendent.children[0]
            if len(descendent.contents) > minimum:
                ancestors.extend(additional_ancestors)
                self.contents[index] = descendent.contents[0]
                descendent.remove(0, ancestors)
                return

            # cai para o filho da esquerda
            additional_ancestors = [(self, index)]
            descendent = self.children[index]
            while descendent.children:
                additional_ancestors.append(
                        (descendent, len(descendent.children) - 1))
                descendent = descendent.children[-1]
            ancestors.extend(additional_ancestors)
            self.contents[index] = descendent.contents[-1]
            descendent.remove(len(descendent.children) - 1, ancestors)
        else:
            self.contents.pop(index)
            if len(self.contents) < minimum and ancestors:
                self.grow(ancestors)

class BTree(object):
    BRANCH = LEAF = _BNode

    def __init__(self, order):
        self.order = order
        self._root = self._bottom = self.LEAF(self)

    def _find_by(self, some_list, field, item):
        l = [x for x in some_list if x[field] == item]
        return True if l else False

        #_find_by(current.contents[index], 0, item)

    def _path_to(self, item):
        current = self._root
        ancestry = []

        while getattr(current, "children", None):
            index = bisect.bisect_left(current.contents, item)
            ancestry.append((current, index))
            if index < len(current.contents) and self._find_by(current.contents, 0, item[0]):
                return ancestry
            current = current.children[index]

        index = bisect.bisect_left(current.contents, item)
        ancestry.append((current, index))
        present = index < len(current.contents)
        present = present and current.contents[index] == item

        return ancestry

    def _present(self, item, ancestors):
        last, index = ancestors[-1]
        return index < len(last.contents) and last.contents[index] == item

    def insert(self, item):
        current = self._root
        ancestors = self._path_to(item)
        node, index = ancestors[-1]
        while getattr(node, "children", None):
            node = node.children[index]
            index = bisect.bisect_left(node.contents, item)
            ancestors.append((node, index))
        node, index = ancestors.pop()
        node.insert(index, item, ancestors)

    def remove(self, item):
        current = self._root
        ancestors = self._path_to(item)

        if self._present(item, ancestors):
            node, index = ancestors.pop()
            node.remove(index, ancestors)
        else:
            raise ValueError("%r not in %s" % (item, self.__class__.__name__))

    def __contains__(self, item):
        return self._present(item, self._path_to(item))

    def __iter__(self):
        def _recurse(node):
            if node.children:
                for child, item in zip(node.children, node.contents):
                    for child_item in _recurse(child):
                        yield child_item
                    yield item
                for child_item in _recurse(node.children[-1]):
                    yield child_item
            else:
                for item in node.contents:
                    yield item

        for item in _recurse(self._root):
            yield item

    def __repr__(self):
        def recurse(node, accum, depth):
            accum.append(("  " * depth) + repr(node))
            for node in getattr(node, "children", []):
                recurse(node, accum, depth + 1)

        accum = []
        recurse(self._root, accum, 0)
        return "\n".join(accum)

    @classmethod
    def bulkload(cls, items, order):
        tree = object.__new__(cls)
        tree.order = order

        leaves = tree._build_bulkloaded_leaves(items)
        tree._build_bulkloaded_branches(leaves)

        return tree

    def _build_bulkloaded_leaves(self, items):
        minimum = self.order // 2
        leaves, seps = [[]], []

        for item in items:
            if len(leaves[-1]) < self.order:
                leaves[-1].append(item)
            else:
                seps.append(item)
                leaves.append([])

        if len(leaves[-1]) < minimum and seps:
            last_two = leaves[-2] + [seps.pop()] + leaves[-1]
            leaves[-2] = last_two[:minimum]
            leaves[-1] = last_two[minimum + 1:]
            seps.append(last_two[minimum])

        return [self.LEAF(self, contents=node) for node in leaves], seps

    def _build_bulkloaded_branches(self, leaves, seps):
        minimum = self.order // 2
        levels = [leaves]

        while len(seps) > self.order + 1:
            items, nodes, seps = seps, [[]], []

            for item in items:
                if len(nodes[-1]) < self.order:
                    nodes[-1].append(item)
                else:
                    seps.append(item)
                    nodes.append([])

            if len(nodes[-1]) < minimum and seps:
                last_two = nodes[-2] + [seps.pop()] + nodes[-1]
                nodes[-2] = last_two[:minimum]
                nodes[-1] = last_two[minimum + 1:]
                seps.append(last_two[minimum])

            offset = 0
            for i, node in enumerate(nodes):
                children = levels[-1][offset:offset + len(node) + 1]
                nodes[i] = self.BRANCH(self, contents=node, children=children)
                offset += len(node) + 1

            levels.append(nodes)

        self._root = self.BRANCH(self, contents=seps, children=levels[-1])

def cleanse(path):
    StepWords = []
    words = []
    wordfreq = []
    gamb = []
    merge = []
    sw = open("/home/eduardo/Área de Trabalho/trab2/stw", "r")   #aqui é pras KayWords
    fop = open(path, "r")  #aqui é o caminho pro texto

    for line in sw:
        for word in line.split():
            StepWords.append(word)              #vetor com StepWords

    for line in fop:
        for word in line.split():
            if word.lower() not in StepWords:
                words.append(word.lower())      #vetor "limpo" e contendo o texto

    #começando a contar a frequencia
    for w in words:
        if w not in gamb:
            gamb.append(w)                  #tem as palvras SEM repetições
            wordfreq.append(words.count(w)) #tem as frequencias

    #inserindo os vetores no merge "zip"
    for i in range(1, len(gamb)):
        merge.append([wordfreq[i], gamb[i]])

    #ordenando a matriz pela coluna de frequencias
    sortedMerge = sorted(merge, key = operator.itemgetter(0))
    sortedMerge.append(path)
    return(sortedMerge)

def _find_by(some_list, field, item):
    l = [x for x in some_list if x[field] == item]
    return True if l else False

if __name__ == '__main__':
    t = []
    texts = []
    guard = []
    print("Informe a tamanho do nó")
    i = int(input())
    b = BTree(i)

    print("Informe a palavra que deseja procurar")
    palavra = str(input())

    for i in range(1, 8):
        o = "/home/eduardo/Área de Trabalho/trab2/txt" + str(i)
        t = cleanse(o)
        b.insert(cleanse(o))
        if _find_by(t, 1, palavra):
            texts.append(o)
            guard.append(t)
    print(texts)
    print("Deseja imprimir os textos que contem a palavra?")
    if input() == "Sim":
        for i in range(0, len(texts)):
            sw = open(texts[i], "r")
            for line in sw:
                print(line)

    print("Deseja remover os textos da árvore?")
    if input() == "Sim":
        for i in range(0, len(guard)-1):
            t = guard[i]
            b.remove(t)

    print(b)
