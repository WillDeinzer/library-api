import bisect
import random

# Selects a random winner from the list of accounts, weighted by the number of reviews they submitted

def choose_winner(accounts_and_counts):
    prefix = []
    total_reviews = 0
    for _, count in accounts_and_counts:
        total_reviews += count
        prefix.append(total_reviews)

    r = random.randint(1, total_reviews)

    index = bisect.bisect_left(prefix, r)
    return accounts_and_counts[index][0] if index < len(accounts_and_counts) else None
    