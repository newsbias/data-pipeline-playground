async def attach_id(id, fut):
    return (id, await fut)


def get_combinations(words, k, output):
    len_to_list_map = {}

    # Split input into a list of words
    n = len(words)

    if not k:
        k = n

    # Loop from 1 to k
    for i in range(1, k+1):

        # List to store strings comprised of i words
        l = set()

        # Loop through all words in input string
        for j in range(0, n-i+1):

            # Base string to add to
            s = ""

            # Add strings of i words to the list
            for z in range(j, j+i):
                s = s + words[z] + " "

            s = s.strip()
            l.add(s)
            if i in len_to_list_map:
                len_to_list_map[i] |= l
            else:
                len_to_list_map[i] = l

    return len_to_list_map
