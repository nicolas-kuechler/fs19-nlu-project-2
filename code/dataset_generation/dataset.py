import pandas as pd
import random
from tqdm import tqdm


def get_train_dataset_true(path_train, shuffle=False):
    """
    
    """

    df = pd.read_csv(path_train, index_col=False)

    ds = []

    print("Processing Training Dataset...")
    for idx, storyid, storytitle, s1, s2, s3, s4, s5 in tqdm(df.itertuples(), total=df.shape[0]):
        story_start = ' '.join([s1, s2, s3, s4])
        
        # generate true sample
        true_story_end = s5
        positive_sample = {"story_start_id":storyid, "story_end_id":storyid, "story_start":story_start, "story_end": true_story_end, "label":1}
        ds.append(positive_sample)
       
    if shuffle:
        random.shuffle(ds)

    return ds

def get_valid_dataset(path_valid, shuffle=True):
    df = pd.read_csv(path_valid, index_col=False)

    ds = []

    print("Processing Valid Dataset...")
    for idx, storyid, s1, s2, s3, s4, ending1, ending2, right_end in tqdm(df.itertuples(), total=df.shape[0]):
        story_start = ' '.join([s1, s2, s3, s4])

        if right_end == 1:
            true_story_end = ending1
            false_story_end = ending2
        elif right_end == 2:
            true_story_end = ending2
            false_story_end = ending1
        else:
            raise ValueError("Not correct end!")

        positive_sample = {"story_start_id":storyid + "_1", "story_end_id":storyid + "_1", "story_start":story_start, "story_end": true_story_end, "label":1}
        ds.append(positive_sample)

        negative_sample = {"story_start_id":storyid + "_1", "story_end_id":storyid + "_0", "story_start":story_start, "story_end": false_story_end, "label":0}
        ds.append(negative_sample)

    if shuffle:
        random.shuffle(ds)

    return ds

def get_crossproduct_dataset_false(path_train, path_mapping, path_names):
    """
    generate a cross product dataset with all endings for a sample frm the file path_train defined in the file path_mapping
    """

    df = pd.read_csv(path_train, index_col=False)

    df_mapping = pd.read_csv(path_mapping, index_col=False, names=['start_idx', 'end_idx'])

    names = pd.read_csv(path_names, index_col=False)
    names = set(names['Name'])

    ds = []

    print("Processing Cross Product Train Dataset...")
    for idx, storyid, storytitle, s1, s2, s3, s4, s5 in tqdm(df.itertuples(), total=df.shape[0]):
        story_start = ' '.join([s1, s2, s3, s4])
        
        # look up which are the 500 most similar 
        sample_mappings = df_mapping.loc[df_mapping['start_idx'] == idx]
        true_story_end = s5

        false_endings = df.loc[sample_mappings['end_idx']][['storyid', 'sentence5']]
       
        # generate all false samples
        for _, false_storyid, false_story_end in tqdm(false_endings.itertuples(), total=false_endings.shape[0]):
            false_story_end = _adjust_false_story_end(story_start=story_start, true_story_end=true_story_end, false_story_end=false_story_end, names=names)
            negative_sample = {"story_start_id":storyid, "story_end_id":false_storyid, "story_start":story_start, "story_end": false_story_end, "label":0}
            ds.append(negative_sample)
        
    return ds

def generate_and_save_init_test_results(path_cross, path_test_results):

    df = pd.read_csv(path_cross, sep='\t', index_col=False)

    n_samples = df.shape[0]

    df = pd.DataFrame(0.5, index=range(n_samples), columns=['prob0', 'prob1'])

    df.to_csv(path_test_results, sep='\t', index=False, header=False)




def _adjust_false_story_end(story_start, true_story_end, false_story_end, names):
    person_story_start = _extract_person(story_start, names)

    # extract person from sampled ending and replace with person of story start
    if person_story_start is not None:
        person_false_story_end = _extract_person(false_story_end, names)
        if person_false_story_end is not None:
            false_story_end = _replace_person(text=false_story_end, old_person=person_false_story_end, new_person=person_story_start)
    
    return false_story_end


def _replace_person(text, old_person, new_person):
    # TODO: use more sophisticated way to change person
    if old_person == 'He' or old_person == 'She' or old_person == 'They' or old_person== 'I':
        return text.replace(old_person + " ", new_person + " ")
    if old_person == 'he' or old_person == 'she' or old_person == 'they':
        return text.replace(" " + old_person + " ", " " + new_person + " ")

    return text.replace(old_person, new_person)

def _extract_person(text, names):
    # TODO: use more sophisticated way to extract person or maybe even multiple people

    # TODO: problem: Ben's does not identify Ben -> USE BERT BASIC TOKENIZER

    persons = set()
    # TODO: use more sophisticated tokenizer (this has problem of Name, and Name.)
    for word in text.split(' '):
        if word in names:
            persons.add(word)

    if len(persons) >= 1:
        for p in persons:
            return p
    else:
        if 'He ' in text:
            return 'He'
        if ' he ' in text:
            return 'he'
        if 'She ' in text:
            return 'She'
        if ' she ' in text:
            return 'she'
        if 'They ' in text:
            return 'They'
        if ' they ' in text:
            return 'they'
        if 'I ' in text:
            return 'I'

def save_dataset_as_tsv(dataset, path):
    df = pd.DataFrame(dataset)
    df.to_csv(path, sep='\t', index=False, columns=['story_start_id', 'story_end_id', 'story_start', 'story_end', 'label'])



def main():
    generate_and_save_init_test_results(path_cross="./data/ds_cross_product_false.tsv",  path_test_results="./data/test_results.tsv")

    ds_train_true = get_train_dataset_true(path_train='./data/train_stories.csv', shuffle=False)
    save_dataset_as_tsv(ds_train_true, path="./data/ds_train_true.tsv")

    ds_valid = get_valid_dataset(path_valid='./data/cloze_test_val__spring2016 - cloze_test_ALL_val.csv', shuffle=False)
    save_dataset_as_tsv(ds_valid, path="./data/ds_valid.tsv")

    ds_cross_product_false = get_crossproduct_dataset_false(path_train='./data/train_stories.csv', path_mapping='./data/train_stories_top_20_most_similar_titles.csv', path_names='./data/first_names.csv')
    save_dataset_as_tsv(ds_cross_product_false, path="./data/ds_cross_product_false.tsv")

if __name__ == '__main__':
    main()