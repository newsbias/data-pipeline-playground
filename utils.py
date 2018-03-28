def get_combinations(elt, k):

    # Split input into a list of words
    words = elt.split()
    n = len(words)

    # Return value - maps from length (int) to list of strings
    len_to_list_map = {}

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
            len_to_list_map[i] = l

    return len_to_list_map

m = get_combinations("Donald Trump and Robert Mueller", 3)
print(m)
