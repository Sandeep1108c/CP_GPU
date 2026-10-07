// Auto-generated nanoGPT configuration for ESP32-S3
// Model: 6L / 8H / 248E

#ifndef NANOGPT_CONFIG_H
#define NANOGPT_CONFIG_H

#define NANOGPT_VOCAB_SIZE  1200
#define NANOGPT_BLOCK_SIZE  160
#define NANOGPT_N_LAYER     6
#define NANOGPT_N_HEAD      8
#define NANOGPT_N_EMBD      248

// Subword string to index mapping
static const char* const NANOGPT_VOCAB[1200] = {
    "<|pad|>", // 0
    "<|culprit|>", // 1
    "<|npc|>", // 2
    "<|trust|>", // 3
    "<|memory|>", // 4
    "<|mood|>", // 5
    "<|input|>", // 6
    "<|response|>", // 7
    "<|end|>", // 8
    "\n", // 9
    " ", // 10
    "!", // 11
    "\"", // 12
    "'", // 13
    ",", // 14
    "-", // 15
    ".", // 16
    "1", // 17
    "2", // 18
    "3", // 19
    ":", // 20
    ";", // 21
    "<", // 22
    ">", // 23
    "?", // 24
    "A", // 25
    "B", // 26
    "C", // 27
    "D", // 28
    "E", // 29
    "F", // 30
    "G", // 31
    "H", // 32
    "I", // 33
    "J", // 34
    "K", // 35
    "L", // 36
    "M", // 37
    "N", // 38
    "O", // 39
    "P", // 40
    "Q", // 41
    "R", // 42
    "S", // 43
    "T", // 44
    "U", // 45
    "V", // 46
    "W", // 47
    "Y", // 48
    "Z", // 49
    "[", // 50
    "]", // 51
    "_", // 52
    "a", // 53
    "b", // 54
    "c", // 55
    "d", // 56
    "e", // 57
    "f", // 58
    "g", // 59
    "h", // 60
    "i", // 61
    "j", // 62
    "k", // 63
    "l", // 64
    "m", // 65
    "n", // 66
    "o", // 67
    "p", // 68
    "q", // 69
    "r", // 70
    "s", // 71
    "t", // 72
    "u", // 73
    "v", // 74
    "w", // 75
    "x", // 76
    "y", // 77
    "z", // 78
    "|", // 79
    "~", // 80
    "—", // 81
    " t", // 82
    "he", // 83
    " a", // 84
    "in", // 85
    "er", // 86
    "ou", // 87
    "on", // 88
    " the", // 89
    " w", // 90
    "en", // 91
    "re", // 92
    " s", // 93
    "at", // 94
    " c", // 95
    "ing", // 96
    " m", // 97
    "is", // 98
    "ed", // 99
    " b", // 100
    "<|", // 101
    "|>", // 102
    " d", // 103
    "es", // 104
    "or", // 105
    " f", // 106
    " I", // 107
    "ar", // 108
    "ti", // 109
    "end", // 110
    "an", // 111
    " th", // 112
    " p", // 113
    " h", // 114
    " n", // 115
    "it", // 116
    " y", // 117
    "as", // 118
    " an", // 119
    "ll", // 120
    " you", // 121
    "ER", // 122
    " o", // 123
    " l", // 124
    " to", // 125
    ".<|", // 126
    "AR", // 127
    "se", // 128
    " in", // 129
    "id", // 130
    "om", // 131
    "ve", // 132
    "al", // 133
    "ot", // 134
    "gh", // 135
    " is", // 136
    "sp", // 137
    "one", // 138
    "hat", // 139
    "ay", // 140
    "ow", // 141
    " T", // 142
    " and", // 143
    " e", // 144
    " be", // 145
    "ght", // 146
    " g", // 147
    "le", // 148
    "ld", // 149
    "ly", // 150
    "tier", // 151
    " of", // 152
    "ic", // 153
    "SH", // 154
    "SHO", // 155
    "SHOP", // 156
    "SHOPK", // 157
    "SHOPKE", // 158
    "SHOPKEE", // 159
    "SHOPKEEP", // 160
    "SHOPKEEPER", // 161
    "ho", // 162
    " ha", // 163
    " was", // 164
    " not", // 165
    "ri", // 166
    " it", // 167
    "oun", // 168
    "out", // 169
    "resp", // 170
    "ver", // 171
    "st", // 172
    "respon", // 173
    "GU", // 174
    "GUAR", // 175
    "GUARD", // 176
    "response", // 177
    " he", // 178
    "et", // 179
    "ce", // 180
    " that", // 181
    " re", // 182
    " k", // 183
    "FAR", // 184
    "FARM", // 185
    "FARMER", // 186
    "ill", // 187
    "OL", // 188
    "OLD", // 189
    "MA", // 190
    "MAN", // 191
    "il", // 192
    "ut", // 193
    "ent", // 194
    "ion", // 195
    " v", // 196
    "ME", // 197
    "MED", // 198
    "MEDI", // 199
    "MEDIU", // 200
    "MEDIUM", // 201
    "ight", // 202
    " st", // 203
    " The", // 204
    " u", // 205
    "ag", // 206
    "ter", // 207
    "ac", // 208
    " r", // 209
    "?<|", // 210
    "LO", // 211
    "LOW", // 212
    "pl", // 213
    " wit", // 214
    " my", // 215
    "ec", // 216
    "ee", // 217
    "ul", // 218
    " for", // 219
    "hing", // 220
    " do", // 221
    "ard", // 222
    "ation", // 223
    "ome", // 224
    "ore", // 225
    " with", // 226
    " me", // 227
    "im", // 228
    " have", // 229
    "HI", // 230
    "HIG", // 231
    "HIGH", // 232
    " con", // 233
    "ef", // 234
    " on", // 235
    "ous", // 236
    "ak", // 237
    " what", // 238
    "ad", // 239
    "oo", // 240
    "ir", // 241
    " are", // 242
    "qu", // 243
    "su", // 244
    "ive", // 245
    " whe", // 246
    "ould", // 247
    "ayer", // 248
    "ro", // 249
    "player", // 250
    "per", // 251
    "ain", // 252
    " as", // 253
    "tion", // 254
    " kn", // 255
    " ab", // 256
    " fr", // 257
    "am", // 258
    "if", // 259
    " tr", // 260
    " night", // 261
    "none", // 262
    " this", // 263
    " sh", // 264
    "ate", // 265
    " at", // 266
    "and", // 267
    "all", // 268
    "cal", // 269
    " about", // 270
    "ound", // 271
    "ious", // 272
    " from", // 273
    "age", // 274
    " coun", // 275
    "!<|", // 276
    "ess", // 277
    "ens", // 278
    " W", // 279
    "ur", // 280
    " or", // 281
    " who", // 282
    "ence", // 283
    " That", // 284
    " know", // 285
    "cil", // 286
    " your", // 287
    " council", // 288
    "ers", // 289
    " ac", // 290
    "est", // 291
    "calm", // 292
    " will", // 293
    " any", // 294
    " ne", // 295
    "el", // 296
    "KI", // 297
    "KID", // 298
    "spic", // 299
    " un", // 300
    "ch", // 301
    "pp", // 302
    " sa", // 303
    "her", // 304
    "spicious", // 305
    " mo", // 306
    "very", // 307
    "ere", // 308
    " A", // 309
    " am", // 310
    "riend", // 311
    "omeone", // 312
    "ell", // 313
    "riendly", // 314
    "The", // 315
    "are", // 316
    "friendly", // 317
    " pat", // 318
    "op", // 319
    "ist", // 320
    "efens", // 321
    " they", // 322
    "efensive", // 323
    "ust", // 324
    "defensive", // 325
    "hop", // 326
    "suspicious", // 327
    " did", // 328
    " lo", // 329
    " vill", // 330
    "ves", // 331
    " shop", // 332
    "ck", // 333
    " ev", // 334
    "ind", // 335
    " gu", // 336
    " village", // 337
    "ol", // 338
    "ep", // 339
    " were", // 340
    " al", // 341
    " B", // 342
    "You", // 343
    "ey", // 344
    " when", // 345
    " su", // 346
    "us", // 347
    " bef", // 348
    " before", // 349
    " pers", // 350
    " can", // 351
    " person", // 352
    " out", // 353
    "ult", // 354
    " would", // 355
    "ast", // 356
    " guard", // 357
    "ant", // 358
    "ap", // 359
    " one", // 360
    " go", // 361
    " ex", // 362
    " tim", // 363
    " wh", // 364
    "ong", // 365
    " H", // 366
    " sp", // 367
    "ame", // 368
    " had", // 369
    " E", // 370
    " com", // 371
    " saw", // 372
    "ect", // 373
    " someone", // 374
    " po", // 375
    "ide", // 376
    " has", // 377
    "thing", // 378
    "ought", // 379
    "ke", // 380
    " but", // 381
    "ough", // 382
    "ack", // 383
    " ar", // 384
    "art", // 385
    "ear", // 386
    " acc", // 387
    "ault", // 388
    " ch", // 389
    " than", // 390
    "ful", // 391
    "eeper", // 392
    " N", // 393
    "idence", // 394
    "ig", // 395
    " vault", // 396
    "ink", // 397
    "res", // 398
    "omet", // 399
    "arm", // 400
    "hed", // 401
    "omething", // 402
    "ble", // 403
    "ie", // 404
    " more", // 405
    " qu", // 406
    "ort", // 407
    " old", // 408
    " S", // 409
    "ft", // 410
    " something", // 411
    "keeper", // 412
    " cl", // 413
    "ra", // 414
    " ri", // 415
    " see", // 416
    "ings", // 417
    "ook", // 418
    "ning", // 419
    " been", // 420
    "who", // 421
    " shopkeeper", // 422
    "ally", // 423
    "rec", // 424
    "ved", // 425
    " j", // 426
    "tern", // 427
    " every", // 428
    " It", // 429
    "ood", // 430
    "der", // 431
    " D", // 432
    "tig", // 433
    "onest", // 434
    "vestig", // 435
    " no", // 436
    " evidence", // 437
    " there", // 438
    " his", // 439
    " think", // 440
    " man", // 441
    " investig", // 442
    "ment", // 443
    "ark", // 444
    " farm", // 445
    " tw", // 446
    "ake", // 447
    " pl", // 448
    " right", // 449
    "te", // 450
    " af", // 451
    " li", // 452
    " des", // 453
    "av", // 454
    " You", // 455
    "ure", // 456
    " theft", // 457
    "tain", // 458
    " them", // 459
    "ge", // 460
    "ther", // 461
    "eop", // 462
    "eople", // 463
    "ull", // 464
    "our", // 465
    " pro", // 466
    " Z", // 467
    " ask", // 468
    " But", // 469
    "what", // 470
    " key", // 471
    " happ", // 472
    "ened", // 473
    " by", // 474
    " wor", // 475
    "can", // 476
    " time", // 477
    "ber", // 478
    "atch", // 479
    " se", // 480
    "ount", // 481
    " like", // 482
    " He", // 483
    " all", // 484
    " M", // 485
    " conf", // 486
    "sed", // 487
    "au", // 488
    " account", // 489
    " two", // 490
    "ser", // 491
    "here", // 492
    "ays", // 493
    "ry", // 494
    " last", // 495
    "leep", // 496
    " le", // 497
    " co", // 498
    " ring", // 499
    "scan", // 500
    "scanor", // 501
    "oro", // 502
    "orm", // 503
    "ting", // 504
    " anything", // 505
    " things", // 506
    " path", // 507
    "iz", // 508
    "tive", // 509
    "ail", // 510
    " bu", // 511
    " str", // 512
    "did", // 513
    " en", // 514
    " if", // 515
    " people", // 516
    " If", // 517
    " ob", // 518
    " rec", // 519
    "th", // 520
    "eak", // 521
    " lock", // 522
    " look", // 523
    "ness", // 524
    "ty", // 525
    " What", // 526
    "ach", // 527
    "avy", // 528
    "wn", // 529
    "side", // 530
    "ted", // 531
    " O", // 532
    " An", // 533
    "un", // 534
    " squ", // 535
    " hand", // 536
    " pr", // 537
    "how", // 538
    " Escanor", // 539
    " after", // 540
    " up", // 541
    "where", // 542
    " say", // 543
    " che", // 544
    " under", // 545
    "day", // 546
    " just", // 547
    " ro", // 548
    "row", // 549
    " without", // 550
    " tell", // 551
    "estion", // 552
    " around", // 553
    " ag", // 554
    " bec", // 555
    " question", // 556
    "What", // 557
    " eas", // 558
    " want", // 559
    "alk", // 560
    "ple", // 561
    " over", // 562
    " lan", // 563
    "ave", // 564
    " patro", // 565
    " back", // 566
    "ance", // 567
    " int", // 568
    " honest", // 569
    " obser", // 570
    " heavy", // 571
    "atc", // 572
    "ose", // 573
    "fer", // 574
    " kid", // 575
    "ew", // 576
    " so", // 577
    " found", // 578
    "me", // 579
    " need", // 580
    " cor", // 581
    " C", // 582
    " happened", // 583
    " too", // 584
    "ace", // 585
    " near", // 586
    "ase", // 587
    "ause", // 588
    "hi", // 589
    "ears", // 590
    "cu", // 591
    "uth", // 592
    " mor", // 593
    " now", // 594
    " heh", // 595
    " patrol", // 596
    " eastern", // 597
    "os", // 598
    " investigation", // 599
    " br", // 600
    " their", // 601
    "ity", // 602
    " morning", // 603
    " car", // 604
    " does", // 605
    "ific", // 606
    "act", // 607
    " trust", // 608
    " fin", // 609
    " mid", // 610
    " care", // 611
    " we", // 612
    " Zoro", // 613
    " could", // 614
    " long", // 615
    " sc", // 616
    " anyone", // 617
    " work", // 618
    " Whe", // 619
    " ta", // 620
    " heard", // 621
    "eep", // 622
    " det", // 623
    "iness", // 624
    " sec", // 625
    " truth", // 626
    " day", // 627
    " Th", // 628
    " ad", // 629
    "oughtful", // 630
    "own", // 631
    "ully", // 632
    " And", // 633
    " im", // 634
    "ated", // 635
    "vers", // 636
    " dis", // 637
    " into", // 638
    "thoughtful", // 639
    " dark", // 640
    "able", // 641
    " most", // 642
    "fic", // 643
    "ree", // 644
    " same", // 645
    "ade", // 646
    " dif", // 647
    " tool", // 648
    "ward", // 649
    " check", // 650
    " years", // 651
    "irec", // 652
    "irm", // 653
    " should", // 654
    "ign", // 655
    "ick", // 656
    "plic", // 657
    " bar", // 658
    " how", // 659
    "ady", // 660
    " L", // 661
    " where", // 662
    " enough", // 663
    " R", // 664
    " Not", // 665
    " They", // 666
    " only", // 667
    "bl", // 668
    " hear", // 669
    "ertain", // 670
    "red", // 671
    " lane", // 672
    " because", // 673
    " case", // 674
    "tic", // 675
    " here", // 676
    "ile", // 677
    "ru", // 678
    " down", // 679
    " mill", // 680
    "ory", // 681
    " thr", // 682
    " through", // 683
    " doing", // 684
    "aster", // 685
    "iet", // 686
    " hour", // 687
    " farmer", // 688
    " wind", // 689
    "ans", // 690
    " make", // 691
    " comple", // 692
    "pt", // 693
    "enti", // 694
    "Did", // 695
    "hy", // 696
    "si", // 697
    " sound", // 698
    " differ", // 699
    " spec", // 700
    "int", // 701
    " asked", // 702
    " wr", // 703
    " confirm", // 704
    " direc", // 705
    "ond", // 706
    " ir", // 707
    " app", // 708
    "ared", // 709
    "reas", // 710
    "ason", // 711
    " el", // 712
    "usiness", // 713
    "night", // 714
    " square", // 715
    "cri", // 716
    " iron", // 717
    " cann", // 718
    " fo", // 719
    " else", // 720
    "irst", // 721
    " pres", // 722
    " gold", // 723
    " yes", // 724
    "ice", // 725
    " beh", // 726
    "ord", // 727
    " descri", // 728
    "ine", // 729
    " tools", // 730
    " midnight", // 731
    "port", // 732
    " while", // 733
    "ang", // 734
    "oth", // 735
    " other", // 736
    " cart", // 737
    " told", // 738
    " per", // 739
    " first", // 740
    " cle", // 741
    "ven", // 742
    "plicate", // 743
    "az", // 744
    "ors", // 745
    "um", // 746
    "wer", // 747
    "form", // 748
    "ief", // 749
    " convers", // 750
    " conversation", // 751
    " op", // 752
    " witness", // 753
    " du", // 754
    " duplicate", // 755
    "ange", // 756
    " specific", // 757
    "ai", // 758
    " him", // 759
    "be", // 760
    " dat", // 761
    "tim", // 762
    "ten", // 763
    " way", // 764
    " investigat", // 765
    " de", // 766
    " everything", // 767
    "eft", // 768
    " hel", // 769
    " walk", // 770
    " act", // 771
    " left", // 772
    " even", // 773
    " help", // 774
    "ild", // 775
    " conn", // 776
    "ary", // 777
    " cannot", // 778
    "uring", // 779
    " some", // 780
    "sing", // 781
    " said", // 782
    " plan", // 783
    "ich", // 784
    " fl", // 785
    " On", // 786
    " ho", // 787
    "identi", // 788
    "ial", // 789
    " different", // 790
    "ner", // 791
    " mark", // 792
    "ield", // 793
    "eel", // 794
    "ited", // 795
    " watch", // 796
    " datte", // 797
    " datteb", // 798
    " dattebay", // 799
    " dattebayo", // 800
    " took", // 801
    "akes", // 802
    "ical", // 803
    " being", // 804
    " made", // 805
    "ever", // 806
    "come", // 807
    "ways", // 808
    " vis", // 809
    " men", // 810
    " feel", // 811
    "honest", // 812
    " then", // 813
    "terday", // 814
    " used", // 815
    "Yes", // 816
    " dr", // 817
    " treas", // 818
    " use", // 819
    " thought", // 820
    "ope", // 821
    " set", // 822
    " sack", // 823
    " gr", // 824
    "aptain", // 825
    " always", // 826
    " outside", // 827
    " nothing", // 828
    "sel", // 829
    "we", // 830
    " may", // 831
    " thief", // 832
    " those", // 833
    " asleep", // 834
    " ser", // 835
    " wheel", // 836
    " Daz", // 837
    " Dazai", // 838
    " ear", // 839
    " very", // 840
    " business", // 841
    " hid", // 842
    "vation", // 843
    "ather", // 844
    " cri", // 845
    " sil", // 846
    " identi", // 847
    "sual", // 848
    " bag", // 849
    " during", // 850
    "spect", // 851
    "ab", // 852
    " knew", // 853
    " show", // 854
    "..", // 855
    "ned", // 856
    " good", // 857
    " own", // 858
    " sm", // 859
    " watc", // 860
    " When", // 861
    " Zer", // 862
    " Zero", // 863
    "ue", // 864
    " sti", // 865
    " suspect", // 866
    " stand", // 867
    " toward", // 868
    "mp", // 869
    " seen", // 870
    "led", // 871
    "ooper", // 872
    " detail", // 873
    "ective", // 874
    "tice", // 875
    "ise", // 876
    " find", // 877
    " bet", // 878
    " came", // 879
    " Someone", // 880
    " window", // 881
    " underst", // 882
    " part", // 883
    " desk", // 884
    " speak", // 885
    " clear", // 886
    "cus", // 887
    "ected", // 888
    " My", // 889
    " sleep", // 890
    " well", // 891
    " exact", // 892
    " mu", // 893
    " which", // 894
    " might", // 895
    "vous", // 896
    " still", // 897
    "fully", // 898
    " build", // 899
    " bel", // 900
    "ving", // 901
    " kind", // 902
    "get", // 903
    " cons", // 904
    " mat", // 905
    " rest", // 906
    " yesterday", // 907
    "outh", // 908
    "mit", // 909
    " never", // 910
    " tax", // 911
    " barn", // 912
    " Ros", // 913
    " Roshi", // 914
    " rout", // 915
    " P", // 916
    "ies", // 917
    " observation", // 918
    " real", // 919
    " cont", // 920
    " full", // 921
    " dist", // 922
    "ages", // 923
    " late", // 924
    "self", // 925
    " field", // 926
    "That", // 927
    "ts", // 928
    " sign", // 929
    "ried", // 930
    "ince", // 931
    " second", // 932
    " rob", // 933
    " carry", // 934
    " pas", // 935
    " wrong", // 936
    "ank", // 937
    "ces", // 938
    " treasur", // 939
    " treasury", // 940
    " come", // 941
    " keep", // 942
    "Do", // 943
    " ans", // 944
    " dec", // 945
    "tell", // 946
    " pre", // 947
    "tle", // 948
    " inv", // 949
    "andages", // 950
    " wag", // 951
    " wagon", // 952
    " expl", // 953
    "Th", // 954
    " get", // 955
    "ween", // 956
    " final", // 957
    "li", // 958
    " reason", // 959
    " point", // 960
    " alone", // 961
    " move", // 962
    "sol", // 963
    " again", // 964
    " complete", // 965
    " behind", // 966
    " past", // 967
    "ative", // 968
    " hold", // 969
    "eli", // 970
    "bery", // 971
    " dra", // 972
    " chap", // 973
    " matter", // 974
    " inform", // 975
    "gan", // 976
    "tions", // 977
    "til", // 978
    "adow", // 979
    " ready", // 980
    "oud", // 981
    " bre", // 982
    "alt", // 983
    " robbery", // 984
    " chapel", // 985
    " name", // 986
    " thing", // 987
    " end", // 988
    " each", // 989
    " motive", // 990
    " shadow", // 991
    "ient", // 992
    "ied", // 993
    "rop", // 994
    "anis", // 995
    "gg", // 996
    " inside", // 997
    " exactly", // 998
    " bought", // 999
    "ute", // 1000
    " G", // 1001
    " us", // 1002
    "ident", // 1003
    "ison", // 1004
    "hes", // 1005
    "aining", // 1006
    " unu", // 1007
    " questions", // 1008
    " quiet", // 1009
    " mis", // 1010
    " inter", // 1011
    "ob", // 1012
    "cl", // 1013
    " norm", // 1014
    " rope", // 1015
    " since", // 1016
    "awn", // 1017
    " requ", // 1018
    "ience", // 1019
    " youn", // 1020
    " young", // 1021
    " unusual", // 1022
    " list", // 1023
    " done", // 1024
    " certain", // 1025
    "ouse", // 1026
    " timing", // 1027
    " ago", // 1028
    " understand", // 1029
    " poison", // 1030
    " bl", // 1031
    " dawn", // 1032
    " land", // 1033
    " carefully", // 1034
    "ird", // 1035
    "ieve", // 1036
    " organ", // 1037
    " organiz", // 1038
    " post", // 1039
    "ex", // 1040
    "inal", // 1041
    "den", // 1042
    "cument", // 1043
    "ced", // 1044
    " sw", // 1045
    "It", // 1046
    " means", // 1047
    "ost", // 1048
    "If", // 1049
    " its", // 1050
    "ually", // 1051
    " pa", // 1052
    " until", // 1053
    " yet", // 1054
    " careful", // 1055
    " whist", // 1056
    " requi", // 1057
    "elcome", // 1058
    " vall", // 1059
    " valley", // 1060
    " corru", // 1061
    " seem", // 1062
    " stay", // 1063
    " everyone", // 1064
    "ently", // 1065
    "air", // 1066
    " ever", // 1067
    " information", // 1068
    "aim", // 1069
    " south", // 1070
    "xt", // 1071
    "ided", // 1072
    " gre", // 1073
    "con", // 1074
    " consist", // 1075
    "arti", // 1076
    " form", // 1077
    " bandages", // 1078
    "nervous", // 1079
    " sure", // 1080
    "ip", // 1081
    "ading", // 1082
    " visit", // 1083
    " talk", // 1084
    " hard", // 1085
    " run", // 1086
    "rious", // 1087
    " Every", // 1088
    " aw", // 1089
    " direction", // 1090
    " less", // 1091
    "gether", // 1092
    " fig", // 1093
    "inc", // 1094
    " document", // 1095
    " proper", // 1096
    " U", // 1097
    " training", // 1098
    "cited", // 1099
    "Welcome", // 1100
    "hey", // 1101
    "Halt", // 1102
    " why", // 1103
    " F", // 1104
    " makes", // 1105
    " small", // 1106
    " exp", // 1107
    "mem", // 1108
    "ater", // 1109
    "open", // 1110
    " offic", // 1111
    " showed", // 1112
    " our", // 1113
    "ither", // 1114
    "excited", // 1115
    " sit", // 1116
    "ud", // 1117
    "eek", // 1118
    "tly", // 1119
    " whistle", // 1120
    "cooper", // 1121
    "cooperative", // 1122
    " today", // 1123
    "Zoro", // 1124
    "My", // 1125
    " usu", // 1126
    " going", // 1127
    " answer", // 1128
    " gen", // 1129
    " stra", // 1130
    " Do", // 1131
    " days", // 1132
    " moved", // 1133
    "ff", // 1134
    " side", // 1135
    " take", // 1136
    "peration", // 1137
    "aces", // 1138
    " road", // 1139
    "artial", // 1140
    " investigating", // 1141
    " Captain", // 1142
    " corrupt", // 1143
    " light", // 1144
    " report", // 1145
    " between", // 1146
    " record", // 1147
    " remem", // 1148
    " useful", // 1149
    " looking", // 1150
    "ery", // 1151
    " rather", // 1152
    "curious", // 1153
    " fam", // 1154
    " In", // 1155
    " This", // 1156
    "ined", // 1157
    " correc", // 1158
    "ish", // 1159
    "ait", // 1160
    " event", // 1161
    " ent", // 1162
    " Now", // 1163
    " normal", // 1164
    " gi", // 1165
    " knows", // 1166
    " whole", // 1167
    " import", // 1168
    " evening", // 1169
    " confirmed", // 1170
    " foll", // 1171
    "ider", // 1172
    "certain", // 1173
    "eliber", // 1174
    "eliberate", // 1175
    "conf", // 1176
    "hys", // 1177
    "hysical", // 1178
    " three", // 1179
    " log", // 1180
    " paper", // 1181
    "bling", // 1182
    " gate", // 1183
    " stone", // 1184
    " place", // 1185
    " mention", // 1186
    " strange", // 1187
    " ste", // 1188
    "orth", // 1189
    " Whether", // 1190
    "od", // 1191
    "pped", // 1192
    " rem", // 1193
    " sounds", // 1194
    " We", // 1195
    " whether", // 1196
    " physical", // 1197
    " connected", // 1198
    " order", // 1199
};

#endif // NANOGPT_CONFIG_H
