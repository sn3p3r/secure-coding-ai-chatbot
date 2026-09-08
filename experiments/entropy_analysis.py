import math
from collections import Counter
import re
import matplotlib.pyplot as plt


def calculate_entropy(text):
    """
    Calculate Shannon entropy for a string.
    """
    if not text:
        return 0.0

    counts = Counter(text)
    total_len = len(text)

    entropy = 0.0

    for count in counts.values():
        probability = count / total_len
        entropy -= probability * math.log2(probability)

    return entropy


# ---------------------------------------------------------
# Read security_utils.py
# ---------------------------------------------------------

with open("security_utils.py", "r", encoding="utf-8") as file:
    code = file.read()


# ---------------------------------------------------------
# Extract "words" / code tokens
# ---------------------------------------------------------
#
# Eg:
#     calculate_entropy
#     password123
#     hashlib
# ---------------------------------------------------------

words = re.findall(r"[A-Za-z0-9_]+", code)



# calculate entropy for every word

entropy_values = []

for word in words:
    entropy = calculate_entropy(word)
    entropy_values.append(entropy)


#result print

print("Shannon Entropy Results")
print("-----------------------")

for word, entropy in zip(words, entropy_values):
    print(f"{word:30} {entropy:.4f}")


# histogram of entropy values

plt.figure(figsize=(10, 6))

plt.hist(
    entropy_values,
    bins=10,
    edgecolor="black"
)

plt.xlabel("Shannon Entropy (bits per character)")
plt.ylabel("Number of Words")
plt.title("Shannon Entropy Distribution of Words in security_utils.py")

plt.tight_layout()

# Save the histogram
plt.savefig("security_utils_entropy_histogram.png", dpi=300)

# Display it
plt.show()