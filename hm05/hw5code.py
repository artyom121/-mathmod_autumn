import numpy as np
from collections import Counter
from sklearn.base import BaseEstimator

def find_best_split(feature_vector, target_vector):
    """
    Находит лучший порог для разделения данных по критерию Джини.

    :param feature_vector: Вектор значений признака.
    :param target_vector: Вектор классов объектов.

    :return thresholds: Отсортированный вектор со всеми возможными порогами.
    :return ginis: Вектор со значениями критерия Джини для каждого порога.
    :return threshold_best: Оптимальный порог.
    :return gini_best: Оптимальное значение критерия Джини.
    """
    # Уникальные значения и их сортировка
    unique_values = np.unique(feature_vector)

    # Параметры для хранения результатов
    thresholds = []
    ginis = []

    # Если уникальных значений меньше 2, нет смысла искать пороги
    if len(unique_values) < 2:
        return thresholds, ginis, None, None

    # Подсчет общего количества объектов и долей классов
    total_count = len(target_vector)
    class_counts = Counter(target_vector)

    # Вычисление начальной энтропии
    initial_gini = 1 - sum((count / total_count) ** 2 for count in class_counts.values())

    # Проход по уникальным значениям для нахождения порогов
    for i in range(len(unique_values) - 1):
        threshold = (unique_values[i] + unique_values[i + 1]) / 2
        left_mask = feature_vector < threshold
        right_mask = ~left_mask

        if np.any(left_mask) and np.any(right_mask):  # Проверяем, что обе подвыборки не пустые
            left_counts = Counter(target_vector[left_mask])
            right_counts = Counter(target_vector[right_mask])

            left_size = left_mask.sum()
            right_size = right_mask.sum()

            # Вычисление Gini для левой и правой подвыборок
            left_gini = 1 - sum((count / left_size) ** 2 for count in left_counts.values())
            right_gini = 1 - sum((count / right_size) ** 2 for count in right_counts.values())

            # Общий Gini для текущего порога
            weighted_gini = (left_size / total_count) * left_gini + (right_size / total_count) * right_gini

            thresholds.append(threshold)
            ginis.append(weighted_gini)

    # Находим лучший порог и соответствующее значение критерия Джини
    if ginis:
        gini_best_index = np.argmin(ginis)
        threshold_best = thresholds[gini_best_index]
        gini_best = ginis[gini_best_index]

        return np.array(thresholds), np.array(ginis), threshold_best, gini_best

    return [], [], None, None
    # ╰( ͡° ͜ʖ ͡° )つ──☆*:・ﾟ

    pass


class DecisionTree(BaseEstimator):
    def __init__(self, feature_types, max_depth=None, min_samples_split=None, min_samples_leaf=None):
        if np.any(list(map(lambda x: x != "real" and x != "categorical", feature_types))):
            raise ValueError("There is unknown feature type")

        self._tree = {}
        self._feature_types = feature_types
        self._max_depth = max_depth
        self._min_samples_split = min_samples_split
        self._min_samples_leaf = min_samples_leaf

    def _fit_node(self, sub_X, sub_y, node):
        # Проверка на терминальный узел
        if len(set(sub_y)) == 1:  # Все объекты одного класса
            node["type"] = "terminal"
            node["class"] = sub_y[0]
            return

        # Проверка на возможность разбить выборку
        feature_best, threshold_best, gini_best, split = None, None, None, None
        for feature in range(sub_X.shape[1]):
            feature_type = self._feature_types[feature]

            if feature_type == "real":
                feature_vector = sub_X[:, feature]
            elif feature_type == "categorical":
                counts = Counter(sub_X[:, feature])
                clicks = Counter(sub_X[sub_y == 1, feature])
                ratio = {key: counts[key] / clicks[key] if key in clicks else 0 for key in counts}
                sorted_categories = sorted(ratio.items(), key=lambda x: x[1])
                categories_map = {cat: idx for idx, (cat, _) in enumerate(sorted_categories)}
                feature_vector = np.array([categories_map[x] for x in sub_X[:, feature]])
            else:
                raise ValueError("Unknown feature type")

            thresholds, ginis = find_best_split(feature_vector, sub_y)
            if gini_best is None or (ginis is not None and ginis.max() > gini_best):
                gini_best = ginis.max()
                feature_best = feature
                threshold_best = thresholds[np.argmax(ginis)]
                split = feature_vector < threshold_best

        # Если не удалось найти подходящее разбиение
        if gini_best is None:
            node["type"] = "terminal"
            node["class"] = Counter(sub_y).most_common(1)[0][0]
            return

        # Создание узла и рекурсивный вызов для дочерних узлов
        node["type"] = "nonterminal"
        node["feature_split"] = feature_best
        node["threshold"] = threshold_best
        node["left_child"], node["right_child"] = {}, {}

        self._fit_node(sub_X[split], sub_y[split], node["left_child"])
        self._fit_node(sub_X[~split], sub_y[~split], node["right_child"])

    def _predict_node(self, x, node):
        if node["type"] == "terminal":
            return node["class"]

        feature_value = x[node["feature_split"]]

        if self._feature_types[node["feature_split"]] == "real":
            if feature_value < node["threshold"]:
                return self._predict_node(x, node["left_child"])
            else:
                return self._predict_node(x, node["right_child"])
        elif self._feature_types[node["feature_split"]] == "categorical":
            category_index = int(feature_value)
            if category_index < node["threshold"]:
                return self._predict_node(x, node["left_child"])
            else:
                return self._predict_node(x, node["right_child"])
        else:
            raise ValueError("Unknown feature type")

    def fit(self, X, y):
        self._fit_node(X, y, self._tree)

    def predict(self, X):
        predicted = []
        for x in X:
            predicted.append(self._predict_node(x, self._tree))
        return np.array(predicted)
