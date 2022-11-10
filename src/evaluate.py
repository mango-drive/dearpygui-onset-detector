import librosa

from audio import *


def load_ground_truth(file):
    # ground truth files from the ENST dataset list the onsets (time, event)
    # time = time of the onset
    # event = abbreviation of the percussive element, eg. bd for bass drum
    with open(file) as f:
        onsets = f.read().splitlines()
        # only extract the onset time
        onsets = [float(onset.split()[0]) for onset in onsets]
    return onsets

def mark_true_positives(ground_truth, onsets, tolerance):
    groundtruth_seen = {o: False for o in ground_truth}
    detected_seen = {o: False for o in onsets}

    for o in onsets:
        # search for a matching onset in the ground truth
        for gt_o in ground_truth:
            diff = round(abs(gt_o - o), 4)
            if diff <= tolerance:
                # if the onset has not been seen yet
                if not groundtruth_seen[gt_o]:
                    # mark the onset in the ground truth as seen
                    groundtruth_seen[gt_o] = True
                    detected_seen[o] = True
                    break
            else:
                continue

    return groundtruth_seen, detected_seen


def count_not_seen(dict):
    return sum([not seen_bool for seen_bool in dict.values()])


def classification_matrix(groundtruth_seen, detected_seen):
    false_negatives = count_not_seen(groundtruth_seen)
    false_positives = count_not_seen(detected_seen)
    true_positives = sum([seen for seen in detected_seen.values()])
    return false_negatives, false_positives, true_positives


def evaluate(ground_truth, detected_onsets, tolerance=0.05):
    groundtruth_seen, detected_seen = mark_true_positives(
        ground_truth, detected_onsets, tolerance
    )

    false_neg, false_pos, true_positives = classification_matrix(
        groundtruth_seen, detected_seen
    )

    precision = true_positives / (true_positives + false_pos)
    recall = true_positives / (true_positives + false_neg)
    f_measure = (2 * precision * recall) / (precision + recall)

    return precision, recall, f_measure

if __name__ == "__main__":
    audio_file = (
        "data/ENST-drums-dataset/drummer_1/036_phrase_disco_simple_slow_sticks.wav"
    )
    ground_truth_file = audio_file.replace('.wav', '.txt')

    print("Loading ground truth...")
    ground_truth = load_ground_truth(ground_truth_file)
    
    print("Loading audio...")
    signal, sr = load_audio(audio_file)

    t = time.time()    
    env, deriv, post, thresh, detected_onsets = detect_onsets(signal, sr=sr, units='time')
    elapsed = time.time() - t

    evaluation = evaluate(ground_truth, detected_onsets)

    print("Our onset detector evaluation:")
    print(evaluation)
    print(f"time elapsed: {elapsed}")

    y, sr = librosa.load(audio_file)

    t = time.time()
    librosa_onsets = librosa.onset.onset_detect(y=y, sr=sr,units='time')
    elapsed = time.time() - t

    evaluation = evaluate(ground_truth, librosa_onsets)
    print("Librosa onset detector evaluation:")
    print(evaluation)
    print(f"time elapsed: {elapsed}")
