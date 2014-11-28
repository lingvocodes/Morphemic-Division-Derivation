import codecs, re, os, operator, time

reStdAfx = re.compile(u'(.*?)([ёуоаяиюэы])?(чь|ть|ти)(\\b|ся|сь)',\
                      flags=re.U)

def strip(word): #this function finds and separates standard affixes
    stem = ''
    standard_affixes = []
    standard_right = ''
    has_suffix = False
    correct_form = True
    left_part = ''
    m = reStdAfx.search(word) #find standard affixes
    if m != None:
        stem = m.group(1)
        if m.group(2) != None:
            has_suffix = True
            stem += m.group(2)
        standard_affixes.append(m.group(3)+'.F')
        if m.group(4) == u'ся' or m.group(4) == u'сь':
            standard_affixes.append('+'+ m.group(4)+'.S')
    else:
        correct_form = False #if nothing found, this is not an infinitive verb
    for affix in standard_affixes:
        standard_right = standard_right + affix
    standard_right = '.S+' + standard_right
    return left_part, stem, standard_right, has_suffix, correct_form

def suffix(prefix_sequence,stem, right_part,points, has_suffix):   #returns a list of all possible word and carries the points from prefix()
    worked = False              #if the word's too short, need to use output of strip()
    suffix_variants = []        #divisions by letters excluding standard affixes
    for i in range(1,len(stem)-1):
        worked = True
        affix = stem[-i:]
        sprava = '.S+' + affix + right_part
        base = stem[:-i]
        suffix_variants.append((prefix_sequence, base, sprava, points))
        suffix_variants += suffix(prefix_sequence, base, sprava, points,has_suffix) #run it again until stem's too short
    if has_suffix == False:
        suffix_variants.append((prefix_sequence, stem, right_part, points))    #this also returns a no-suffix option
    if worked == False:
        return [(prefix_sequence, stem,right_part,points)]
    else:
        return suffix_variants

def prefix(left_part, stem, right_part, has_suffix): #returns a list of all possible divisiona from the left
    prefix_variants = []
    if has_suffix == True:
        k = 2
    else:
        k = 1
    for i in range (1,len(stem)-k):
        affix = stem[:i]
        prefix_sequence = left_part + affix + '.P+'
        base = stem[i:]
        prefix_variants.append((prefix_sequence, base, right_part))
        prefix_variants += prefix(prefix_sequence, base, right_part, has_suffix)
    return prefix_variants

def dict_import(): #imports csv dictionaries into the program
    dict_list = {}              #this has all the dictionaries
    for root, dirs, files in os.walk(u'./dict'):
        for item in files:
            current_dict = {}   #this stores one dictionary at a time
            if item.endswith(u'.csv'):
                f = codecs.open(root+'/'+item,'r','utf-8') #open the csv
                if item == 'roots_na.csv':
                    for line in f:
                        koren = line.strip('\r\n')
                        current_dict[koren] = '1000' #this is where points for roots come from
                    dict_list[item[:-4]] = current_dict
                else:
                    for line in f:
                        affix,frequency = line.split(';')
                        current_dict[affix] = frequency.strip('\r\n') #adds the pairs to current dictionary
                    dict_list[item[:-4]] = current_dict #now dict_list has dictionary name : {affix : frequency}
                f.close()
    return dict_list


def check_in_dict(dict_list,affix,dictionary): #this assigns points
    points = 1
    prefix_coeff = {1:20,2:49,3:23,4:7} #data from stats csv, times 100
    suffix_coeff = {1:52,2:38,3:0.3,4:0.01} #this is length stats
    if dictionary == 'verb_prefix':
        current_coeff = prefix_coeff
    elif dictionary == 'verb_suffix':
        current_coeff = suffix_coeff
    try:
        number = float(dict_list[dictionary][affix])
    except KeyError:   # if there is no such key in the dictionary
        return points
    if dictionary == 'roots_na':
        points = number * len(affix) * len(affix)
    else:
        if len(affix) > 4:
            mult = 0.001
        else:
            mult = current_coeff[len(affix)]
        points = mult * number * len(affix) * len(affix)
    return points

def prefix_eval(prefix_sequence): #this evaluates a given prefix sequence
    prefixes = prefix_sequence.split('.P+')
    chain_coeff = {0:12,1:78,2:9,3:0.5} #this is a number of prefixes data
    lower = evil_suffix_killer(prefixes)
    if len(prefixes)-1 > 2:
        return 0
    points = 0
    for item in prefixes:
        if len(item) > 4:
            lower = lower / 10
        points += check_in_dict(dict_list,item,'verb_prefix')
    return int(points * chain_coeff[len(prefixes)-1] * lower)

def suffix_eval(base,sprava,points): #this evaluates a given suffix sequence
    suffixes = sprava.split('.S+')   #this function has a root check
    suffixes = suffixes[:-1]
    lower = evil_suffix_killer(suffixes)
    if has_suffix == True:
        chain_coeff = {0:0,1:53,2:28,3:15,4:3,5:0.1} #this is a number of suffixes data
    else:
        chain_coeff = {0:53,1:28,2:15,3:3,4:0.1,5:0.1} #if has no -V- suffix, use reduced values
    if len(suffixes)-1 > 5:
        return points
    root_check = check_in_dict(dict_list,base,'roots_na')
    for item in suffixes:
        if len(item) > 4:
            return 0
        points += check_in_dict(dict_list,item,'verb_suffix')
    points = int(points * root_check * chain_coeff[len(suffixes)-1] / lower)
    return points

def first_run_prefix(prefix_variants):
    legit_prefixes = []
    for prefix_sequence, base, right_part in prefix_variants:   #try to find prefixes
        points = prefix_eval(prefix_sequence)
        if points > 100000: #if some options are more likely than others, use only them
            legit_prefixes.append((prefix_sequence,base,right_part,points))
    return legit_prefixes

def evil_suffix_killer(suffixes): #this is named after a desperate attempt to fix a minor bug
    counter = 0                   #protection against illegitimate one-letter suffix chains
    for i in range(len(suffixes)):
        try:
            if len(suffixes[i]) == 1 and len(suffixes[i+1]) == 1:
                counter += 1
        except:
            break
    if counter == 0:
        return 1
    return 10 ** (counter-1)

time_start = time.clock()
dict_list = dict_import()
testing = codecs.open('input.csv','r','utf-8') #change the name of input files here
log = codecs.open('log.csv','w','utf-8')
words = []
counter = 0
incorrect_counter = 0
for line in testing:    #this creates a list of verbs from the csv
    counter += 1
    if counter % 1 != 0:#_change_ the number of verbs to run
        continue
    verb, ideal = line.split(';')
    ideal = ideal.strip('\r\n')
    words.append((verb,ideal))
success = 0
total = 0
for verb, ideal in words:
    left_part,stem,standard_right,has_suffix,correct_form = strip(verb)
    if correct_form == False:
        log.write(verb + ';'+ ideal + ';'+ 'incorrect form'+'\r\n') #remove incorrect forms
        incorrect_counter += 1
        continue
    #the prefix check starts here
    prefix_variants = prefix(left_part, stem, standard_right,has_suffix)   #divide prefixes
    legit_prefixes = first_run_prefix(prefix_variants)          #check if found good matches
    legit_prefixes.append((left_part,stem,standard_right,0))
    suffix_variants = []
    if legit_prefixes != []:                                    #this creates suffix variants
        for prefix_sequence, base, right_part, points in legit_prefixes:
            suffix_variants += suffix(prefix_sequence,base,right_part,points,has_suffix)
    else:
        points = 0
        prefix_sequence = ''
        suffix_variants = suffix(prefix_sequence,stem,standard_right, points, has_suffix)
    #the suffix check starts here
    options = {}
    for prefix_sequence, base, sprava, points in suffix_variants:
        new_points = suffix_eval(base,sprava,points)
        base = base + '.R+'
        options[prefix_sequence+base+sprava] = new_points
    #output
    sorted_options = sorted(options.iteritems(), reverse = True,key = operator.itemgetter(1))
    for option, points in sorted_options:
        option = option.replace(u'.R+.S+',u'.R+')
        option = option.replace(u'+ова.S',u'+ов.S+а.S')
        if option == ideal:
            log.write(verb + ';' + option + ';' + '1' + ';' + '\r\n')
            success += 1
        else:
            log.write(verb + ';' + ideal + ';' + '0' + ';'+ option + '\r\n')
        total += 1
        if total % 500 == 0: #this indicates work progress in console
            time_current = time.clock()
            elapsed = (time_current - time_start)/60
            print 'words done: ', total, ' elapsed time (min): ', elapsed
        break
print 'FINISHED!'
log.write('success: ' + str(success) + ' total: ' + str(total) + ' percentage: ' + str(success * 100 /(total-incorrect_counter)) + ';;;'+ '\r\n')
log.close()
testing.close()
