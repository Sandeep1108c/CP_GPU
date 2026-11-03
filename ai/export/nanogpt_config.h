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
    "%", // 12
    "'", // 13
    ",", // 14
    "-", // 15
    ".", // 16
    "0", // 17
    "1", // 18
    "2", // 19
    "3", // 20
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
    "_", // 50
    "a", // 51
    "b", // 52
    "c", // 53
    "d", // 54
    "e", // 55
    "f", // 56
    "g", // 57
    "h", // 58
    "i", // 59
    "j", // 60
    "k", // 61
    "l", // 62
    "m", // 63
    "n", // 64
    "o", // 65
    "p", // 66
    "q", // 67
    "r", // 68
    "s", // 69
    "t", // 70
    "u", // 71
    "v", // 72
    "w", // 73
    "x", // 74
    "y", // 75
    "z", // 76
    "|", // 77
    "~", // 78
    "—", // 79
    " t", // 80
    "he", // 81
    "er", // 82
    "nd", // 83
    " a", // 84
    "ou", // 85
    " the", // 86
    "in", // 87
    " s", // 88
    " w", // 89
    "ti", // 90
    "end", // 91
    " c", // 92
    "or", // 93
    "ar", // 94
    "tier", // 95
    "<|", // 96
    "|>", // 97
    "ER", // 98
    "AR", // 99
    " m", // 100
    " b", // 101
    " d", // 102
    "at", // 103
    "ed", // 104
    "on", // 105
    "ing", // 106
    "hi", // 107
    "en", // 108
    "as", // 109
    "re", // 110
    " f", // 111
    "an", // 112
    " y", // 113
    "al", // 114
    "el", // 115
    " o", // 116
    "id", // 117
    "es", // 118
    "!<|", // 119
    " i", // 120
    " you", // 121
    " l", // 122
    " in", // 123
    " p", // 124
    "EE", // 125
    "SH", // 126
    "SHO", // 127
    "SHOP", // 128
    "SHOPK", // 129
    "SHOPKEE", // 130
    "SHOPKEEP", // 131
    "SHOPKEEPER", // 132
    "ro", // 133
    "GU", // 134
    "GUAR", // 135
    "GUARD", // 136
    " g", // 137
    "FAR", // 138
    "FARM", // 139
    "FARMER", // 140
    "us", // 141
    "ho", // 142
    ".<|", // 143
    "OL", // 144
    "OLD", // 145
    "MA", // 146
    "MAN", // 147
    "ous", // 148
    "th", // 149
    "ri", // 150
    "ve", // 151
    "ic", // 152
    "ha", // 153
    " st", // 154
    "il", // 155
    " and", // 156
    " to", // 157
    " he", // 158
    " n", // 159
    " was", // 160
    "gh", // 161
    "ly", // 162
    "ef", // 163
    "LO", // 164
    "LOW", // 165
    "ME", // 166
    "MED", // 167
    "MEDI", // 168
    "MEDIU", // 169
    "MEDIUM", // 170
    "HI", // 171
    "HIG", // 172
    "HIGH", // 173
    "ra", // 174
    "le", // 175
    "ke", // 176
    " v", // 177
    "hat", // 178
    "ter", // 179
    "ck", // 180
    " hi", // 181
    " I", // 182
    "ght", // 183
    "ld", // 184
    " my", // 185
    " of", // 186
    "ay", // 187
    " is", // 188
    " an", // 189
    "usp", // 190
    " ha", // 191
    "si", // 192
    "ag", // 193
    "ch", // 194
    "ver", // 195
    "ul", // 196
    "st", // 197
    "ner", // 198
    "one", // 199
    "ensi", // 200
    "ici", // 201
    "sc", // 202
    "ight", // 203
    "cal", // 204
    "The", // 205
    "uspici", // 206
    "et", // 207
    "ec", // 208
    " Z", // 209
    "uspicious", // 210
    " wi", // 211
    "fri", // 212
    "friend", // 213
    "friendly", // 214
    "calm", // 215
    "suspicious", // 216
    "def", // 217
    "defensi", // 218
    "defensive", // 219
    "nerv", // 220
    "nervous", // 221
    "Esc", // 222
    "Escan", // 223
    "Escanor", // 224
    " ke", // 225
    "KI", // 226
    "KID", // 227
    " e", // 228
    "oo", // 229
    "ard", // 230
    "aul", // 231
    "ow", // 232
    " key", // 233
    " D", // 234
    " his", // 235
    "out", // 236
    " vaul", // 237
    " vault", // 238
    " with", // 239
    "ai", // 240
    "os", // 241
    " it", // 242
    " u", // 243
    "did", // 244
    "ound", // 245
    " on", // 246
    "me", // 247
    "what", // 248
    " Escanor", // 249
    "ut", // 250
    "oro", // 251
    "pt", // 252
    " for", // 253
    "ce", // 254
    "who", // 255
    " al", // 256
    " ar", // 257
    " me", // 258
    " R", // 259
    " thi", // 260
    " cou", // 261
    "ep", // 262
    " sa", // 263
    " whe", // 264
    "ol", // 265
    "oshi", // 266
    "az", // 267
    " do", // 268
    " go", // 269
    "ur", // 270
    "azai", // 271
    " Roshi", // 272
    "ate", // 273
    " h", // 274
    " Zoro", // 275
    " coun", // 276
    "ru", // 277
    "whe", // 278
    "aster", // 279
    "ell", // 280
    "ock", // 281
    " can", // 282
    "is", // 283
    " fro", // 284
    " counc", // 285
    " council", // 286
    " from", // 287
    " at", // 288
    "arm", // 289
    "atch", // 290
    " no", // 291
    "ide", // 292
    "art", // 293
    "ron", // 294
    "ere", // 295
    " ro", // 296
    " Dazai", // 297
    " th", // 298
    "ak", // 299
    "qu", // 300
    " are", // 301
    "ill", // 302
    "ad", // 303
    " hand", // 304
    " heh", // 305
    " gold", // 306
    " did", // 307
    " cl", // 308
    "te", // 309
    " cha", // 310
    "where", // 311
    " be", // 312
    "ain", // 313
    " bar", // 314
    "wn", // 315
    " un", // 316
    " any", // 317
    "av", // 318
    "how", // 319
    " re", // 320
    " that", // 321
    "pp", // 322
    " se", // 323
    " were", // 324
    " farm", // 325
    " cane", // 326
    " night", // 327
    "tive", // 328
    "ast", // 329
    " wheel", // 330
    "se", // 331
    "pl", // 332
    "bout", // 333
    "thing", // 334
    " old", // 335
    " hid", // 336
    " Zer", // 337
    " Zero", // 338
    "agon", // 339
    "mb", // 340
    "ry", // 341
    " chap", // 342
    " chapel", // 343
    "ore", // 344
    "to", // 345
    " gu", // 346
    "ear", // 347
    " iron", // 348
    " wagon", // 349
    "per", // 350
    " H", // 351
    "Master", // 352
    " lock", // 353
    "mor", // 354
    "reas", // 355
    "avy", // 356
    "ent", // 357
    " this", // 358
    "row", // 359
    " dat", // 360
    "ome", // 361
    " che", // 362
    "ood", // 363
    " they", // 364
    " your", // 365
    " datte", // 366
    " datteb", // 367
    " dattebay", // 368
    " dattebayo", // 369
    " armor", // 370
    " about", // 371
    "etec", // 372
    " heavy", // 373
    "king", // 374
    " ta", // 375
    " co", // 376
    " The", // 377
    "and", // 378
    " us", // 379
    "it", // 380
    "etective", // 381
    " fi", // 382
    "ery", // 383
    " du", // 384
    "cks", // 385
    "plic", // 386
    " guard", // 387
    "ened", // 388
    " ri", // 389
    "ac", // 390
    " N", // 391
    "ll", // 392
    " tra", // 393
    " who", // 394
    " duplic", // 395
    " duplicate", // 396
    "side", // 397
    " whi", // 398
    "que", // 399
    "mp", // 400
    "idn", // 401
    "apt", // 402
    "aptain", // 403
    " into", // 404
    "bb", // 405
    "age", // 406
    " midn", // 407
    " midnight", // 408
    "ning", // 409
    "ok", // 410
    " des", // 411
    " found", // 412
    " see", // 413
    " cart", // 414
    " watch", // 415
    " sp", // 416
    " W", // 417
    "ng", // 418
    "Captain", // 419
    "tell", // 420
    "ins", // 421
    "ure", // 422
    " loo", // 423
    " vill", // 424
    "hed", // 425
    " out", // 426
    " pa", // 427
    "ess", // 428
    " tw", // 429
    " two", // 430
    " young", // 431
    "ts", // 432
    " mor", // 433
    " chi", // 434
    " Detective", // 435
    " saw", // 436
    " door", // 437
    " stra", // 438
    " chest", // 439
    " paper", // 440
    "ley", // 441
    "ect", // 442
    " morning", // 443
    " as", // 444
    " desk", // 445
    " barn", // 446
    " ev", // 447
    " dra", // 448
    " mo", // 449
    "rou", // 450
    " last", // 451
    "all", // 452
    " po", // 453
    "ence", // 454
    " not", // 455
    "ack", // 456
    " k", // 457
    " Master", // 458
    "ever", // 459
    "hind", // 460
    " anything", // 461
    " ho", // 462
    "bar", // 463
    " He", // 464
    "leep", // 465
    "sel", // 466
    " thief", // 467
    " op", // 468
    "ist", // 469
    " used", // 470
    " took", // 471
    " tax", // 472
    " behind", // 473
    " by", // 474
    " cid", // 475
    " cider", // 476
    "ty", // 477
    " mar", // 478
    "go", // 479
    " bu", // 480
    "omeone", // 481
    " treas", // 482
    "outh", // 483
    " A", // 484
    "ers", // 485
    "ling", // 486
    "arut", // 487
    "aruto", // 488
    "ake", // 489
    "nder", // 490
    "ves", // 491
    "very", // 492
    "hop", // 493
    " while", // 494
    " inside", // 495
    " sh", // 496
    " gra", // 497
    " handc", // 498
    " handcart", // 499
    " robb", // 500
    " stol", // 501
    " stolen", // 502
    " ti", // 503
    "My", // 504
    " ste", // 505
    " south", // 506
    " all", // 507
    "ant", // 508
    " r", // 509
    "ir", // 510
    " sil", // 511
    "den", // 512
    "ge", // 513
    " or", // 514
    "day", // 515
    "our", // 516
    " lan", // 517
    " robbery", // 518
    "are", // 519
    " ru", // 520
    " village", // 521
    "ne", // 522
    " br", // 523
    "ass", // 524
    " S", // 525
    " susp", // 526
    " own", // 527
    " armory", // 528
    " dow", // 529
    " down", // 530
    "her", // 531
    "ury", // 532
    "efore", // 533
    " has", // 534
    " oil", // 535
    " sacks", // 536
    " heard", // 537
    " Naruto", // 538
    "ones", // 539
    " suspect", // 540
    " Captain", // 541
    " happ", // 542
    " mu", // 543
    " ac", // 544
    " af", // 545
    " had", // 546
    " treasury", // 547
    "ting", // 548
    " before", // 549
    " hidden", // 550
    "ig", // 551
    " G", // 552
    "ick", // 553
    " after", // 554
    "ought", // 555
    " under", // 556
    " stone", // 557
    " sk", // 558
    " skel", // 559
    " skelet", // 560
    " skeleton", // 561
    " am", // 562
    " happened", // 563
    " fl", // 564
    "pe", // 565
    " wal", // 566
    "eld", // 567
    " aw", // 568
    " B", // 569
    " li", // 570
    " sha", // 571
    " mill", // 572
    "ked", // 573
    " him", // 574
    "ank", // 575
    " bought", // 576
    " bro", // 577
    " de", // 578
    "ward", // 579
    "ink", // 580
    " right", // 581
    " up", // 582
    " shad", // 583
    "eli", // 584
    "Zoro", // 585
    "ower", // 586
    " sound", // 587
    " bone", // 588
    " shadow", // 589
    " di", // 590
    "ted", // 591
    " bl", // 592
    "ocked", // 593
    " sque", // 594
    "ree", // 595
    " toward", // 596
    " hear", // 597
    "ester", // 598
    "esterday", // 599
    " back", // 600
    " straight", // 601
    " lef", // 602
    " left", // 603
    "andag", // 604
    " shop", // 605
    " T", // 606
    "ched", // 607
    " brass", // 608
    " cor", // 609
    " never", // 610
    "No", // 611
    "tique", // 612
    " but", // 613
    " evid", // 614
    " evidence", // 615
    "um", // 616
    " over", // 617
    " chisel", // 618
    "ye", // 619
    " chests", // 620
    " master", // 621
    " one", // 622
    " gre", // 623
    " ch", // 624
    " antique", // 625
    " silver", // 626
    " wat", // 627
    " mis", // 628
    "atro", // 629
    "They", // 630
    " squeak", // 631
    " dry", // 632
    " day", // 633
    " bandag", // 634
    " kn", // 635
    " brok", // 636
    " broken", // 637
    " steal", // 638
    "hy", // 639
    " yesterday", // 640
    " sc", // 641
    " when", // 642
    " its", // 643
    " river", // 644
    " char", // 645
    "ft", // 646
    "~<|", // 647
    " unl", // 648
    " unlocked", // 649
    " ago", // 650
    " opened", // 651
    "pa", // 652
    " oat", // 653
    "eps", // 654
    " nor", // 655
    "ice", // 656
    "ading", // 657
    " tool", // 658
    " tools", // 659
    " crow", // 660
    " crowbar", // 661
    " miss", // 662
    " watcht", // 663
    " watchtower", // 664
    " arc", // 665
    " archi", // 666
    " archiv", // 667
    " archivist", // 668
    "am", // 669
    " val", // 670
    " asleep", // 671
    " wood", // 672
    " wooden", // 673
    " dar", // 674
    "res", // 675
    " ex", // 676
    " corru", // 677
    " corrupt", // 678
    " cry", // 679
    " crypt", // 680
    "iness", // 681
    "tic", // 682
    " L", // 683
    " por", // 684
    " sw", // 685
    " like", // 686
    "les", // 687
    " every", // 688
    "pped", // 689
    " valley", // 690
    " near", // 691
    " around", // 692
    " shadows", // 693
    "round", // 694
    "li", // 695
    " off", // 696
    " ra", // 697
    " tru", // 698
    "ance", // 699
    "ears", // 700
    "tt", // 701
    "tten", // 702
    " charter", // 703
    " E", // 704
    " only", // 705
    " dark", // 706
    " say", // 707
    " sto", // 708
    " loot", // 709
    " patro", // 710
    " forty", // 711
    " bandages", // 712
    "ame", // 713
    "ely", // 714
    " anyone", // 715
    "ving", // 716
    " have", // 717
    "..", // 718
    "tion", // 719
    "you", // 720
    "ust", // 721
    " porch", // 722
    " past", // 723
    "rand", // 724
    "randpa", // 725
    "air", // 726
    "ind", // 727
    "rough", // 728
    "ried", // 729
    " diz", // 730
    " dizz", // 731
    " car", // 732
    "tern", // 733
    "ved", // 734
    " pois", // 735
    " poison", // 736
    "ned", // 737
    " lane", // 738
    "was", // 739
    " alone", // 740
    " without", // 741
    "bye", // 742
    "thank", // 743
    "elie", // 744
    "elieve", // 745
    " tip", // 746
    " inner", // 747
    " wheeled", // 748
    " rope", // 749
    " O", // 750
    "ouch", // 751
    " through", // 752
    "any", // 753
    "ks", // 754
    " walking", // 755
    " j", // 756
    " gate", // 757
    " le", // 758
    " pl", // 759
    " alley", // 760
    "usiness", // 761
    " know", // 762
    " en", // 763
    "bi", // 764
    "ath", // 765
    "ps", // 766
    "ost", // 767
    " someone", // 768
    " missing", // 769
    "mbling", // 770
    "wheel", // 771
    " cro", // 772
    "He", // 773
    " years", // 774
    "eper", // 775
    "hen", // 776
    " dro", // 777
    "Farm", // 778
    "Farmer", // 779
    " truth", // 780
    " ow", // 781
    "ged", // 782
    " straw", // 783
    " marti", // 784
    " martial", // 785
    " tu", // 786
    " cat", // 787
    " catac", // 788
    " cataco", // 789
    " catacomb", // 790
    "barrow", // 791
    " buy", // 792
    "?<|", // 793
    "good", // 794
    " qu", // 795
    " foo", // 796
    "ual", // 797
    "ee", // 798
    " sn", // 799
    " da", // 800
    " open", // 801
    " pro", // 802
    " so", // 803
    " su", // 804
    " Y", // 805
    " away", // 806
    "ab", // 807
    " tracks", // 808
    " ga", // 809
    "mber", // 810
    " drain", // 811
    " stair", // 812
    " stairs", // 813
    " store", // 814
    "ings", // 815
    "wer", // 816
    " dr", // 817
    " dri", // 818
    "rime", // 819
    "ther", // 820
    "ride", // 821
    "onest", // 822
    " stole", // 823
    "onf", // 824
    "hal", // 825
    "Dazai", // 826
    " latch", // 827
    " what", // 828
    " shin", // 829
    " It", // 830
    " Heh", // 831
    "ci", // 832
    " forgo", // 833
    " forgotten", // 834
    "anis", // 835
    " dawn", // 836
    " vi", // 837
    " dizzy", // 838
    " spi", // 839
    " spiked", // 840
    "of", // 841
    " water", // 842
    " bre", // 843
    "ot", // 844
    "ook", // 845
    " hay", // 846
    "Us", // 847
    " chim", // 848
    " chimne", // 849
    " chimney", // 850
    "hing", // 851
    " ruins", // 852
    "esw", // 853
    "eswa", // 854
    "eswax", // 855
    "Someone", // 856
    " time", // 857
    " fif", // 858
    "oth", // 859
    " honest", // 860
    " town", // 861
    " amber", // 862
    " greas", // 863
    " grease", // 864
    " grave", // 865
    " gravey", // 866
    " graveyard", // 867
    " handle", // 868
    "inal", // 869
    " business", // 870
    "ong", // 871
    " My", // 872
    "fe", // 873
    " prou", // 874
    " proud", // 875
    " where", // 876
    " hoo", // 877
    " hiding", // 878
    " check", // 879
    " patrol", // 880
    " north", // 881
    " lantern", // 882
    "keeper", // 883
    " get", // 884
    " pick", // 885
    "were", // 886
    "tice", // 887
    "ough", // 888
    " clu", // 889
    " rece", // 890
    " recei", // 891
    " receipt", // 892
    "ould", // 893
    " sec", // 894
    " marks", // 895
    "uts", // 896
    " wide", // 897
    "ret", // 898
    " Grandpa", // 899
    " ben", // 900
    " bene", // 901
    " beneath", // 902
    " whal", // 903
    " whale", // 904
    " beeswax", // 905
    " much", // 906
    " sounds", // 907
    " our", // 908
    " spic", // 909
    " spiced", // 910
    " per", // 911
    " drink", // 912
    "ose", // 913
    " sm", // 914
    "It", // 915
    " hor", // 916
    " motive", // 917
    "eed", // 918
    "ally", // 919
    " cell", // 920
    " cellar", // 921
    " keys", // 922
    "use", // 923
    "ces", // 924
    "led", // 925
    " nin", // 926
    " ninj", // 927
    " ninja", // 928
    " bal", // 929
    " IO", // 930
    " IOUs", // 931
    " their", // 932
    "ening", // 933
    "ouse", // 934
    " drawer", // 935
    " You", // 936
    "ses", // 937
    " waterwheel", // 938
    " fra", // 939
    " clay", // 940
    " eag", // 941
    " tak", // 942
    " taken", // 943
    " acc", // 944
    " ali", // 945
    " alibi", // 946
    " fall", // 947
    " sleep", // 948
    "vel", // 949
    " eld", // 950
    " nothing", // 951
    " haul", // 952
    "gain", // 953
    " flas", // 954
    " flask", // 955
    "arp", // 956
    " wo", // 957
    "ff", // 958
    "sts", // 959
    " well", // 960
    " gambling", // 961
    " alt", // 962
    " altar", // 963
    " her", // 964
    "hey", // 965
    "lling", // 966
    " qui", // 967
    " quiet", // 968
    " sure", // 969
    " notice", // 970
    "aim", // 971
    " three", // 972
    " pay", // 973
    " taxes", // 974
    " think", // 975
    " deb", // 976
    " want", // 977
    "ian", // 978
    " Li", // 979
    " ruts", // 980
    " farmer", // 981
    "house", // 982
    " mud", // 983
    " them", // 984
    " Go", // 985
    " greav", // 986
    " greaves", // 987
    " eagle", // 988
    " bad", // 989
    " badge", // 990
    " loose", // 991
    " pensi", // 992
    " pension", // 993
    " bur", // 994
    " villag", // 995
    " villagers", // 996
    " canv", // 997
    " canvas", // 998
    "ang", // 999
    "nly", // 1000
    " make", // 1001
    "ven", // 1002
    "iant", // 1003
    " pry", // 1004
    "ea", // 1005
    " detective", // 1006
    "ecl", // 1007
    " tun", // 1008
    " tunn", // 1009
    " tunnel", // 1010
    "gat", // 1011
    "gating", // 1012
    " That", // 1013
    "ced", // 1014
    "ze", // 1015
    " whole", // 1016
    " unus", // 1017
    " unusual", // 1018
    " light", // 1019
    "self", // 1020
    "dy", // 1021
    " lose", // 1022
    " cle", // 1023
    " Watch", // 1024
    "als", // 1025
    "hopkeeper", // 1026
    " Believe", // 1027
    " awake", // 1028
    " secret", // 1029
    " clan", // 1030
    " clanking", // 1031
    " stag", // 1032
    "Wel", // 1033
    "Welc", // 1034
    "Welcome", // 1035
    " name", // 1036
    " bol", // 1037
    " wind", // 1038
    " steps", // 1039
    " been", // 1040
    " prime", // 1041
    "ation", // 1042
    " debts", // 1043
    " again", // 1044
    "Hal", // 1045
    "Halt", // 1046
    " Lion", // 1047
    " ou", // 1048
    " outer", // 1049
    " bec", // 1050
    " What", // 1051
    "Hey", // 1052
    " em", // 1053
    " empt", // 1054
    " empty", // 1055
    " fifty", // 1056
    " crown", // 1057
    " crowns", // 1058
    "the", // 1059
    " When", // 1060
    " whist", // 1061
    " find", // 1062
    " clues", // 1063
    " sack", // 1064
    " horse", // 1065
    "onfess", // 1066
    "inn", // 1067
    " wall", // 1068
    "ause", // 1069
    "ild", // 1070
    " then", // 1071
    "aked", // 1072
    " field", // 1073
    " fields", // 1074
    " bales", // 1075
    " taver", // 1076
    " tavern", // 1077
    " pus", // 1078
    "der", // 1079
    " black", // 1080
    " la", // 1081
    " lamp", // 1082
    "reet", // 1083
    "your", // 1084
    " easter", // 1085
    " eastern", // 1086
    " outside", // 1087
    " foot", // 1088
    " footst", // 1089
    "aces", // 1090
    " barrow", // 1091
    " driving", // 1092
    " other", // 1093
    " ly", // 1094
    " lying", // 1095
    " Even", // 1096
    " guardian", // 1097
    "uring", // 1098
    "pping", // 1099
    "ges", // 1100
    " heading", // 1101
    " very", // 1102
    " sick", // 1103
    "ared", // 1104
    " squeaky", // 1105
    " steel", // 1106
    "Go", // 1107
    " dice", // 1108
    " carved", // 1109
    " inves", // 1110
    " investi", // 1111
    " investigating", // 1112
    " whistle", // 1113
    " would", // 1114
    "...", // 1115
    " buyer", // 1116
    "ded", // 1117
    " coat", // 1118
    " lou", // 1119
    " loud", // 1120
    " stand", // 1121
    "ns", // 1122
    "itting", // 1123
    " train", // 1124
    " training", // 1125
    " shiny", // 1126
    " way", // 1127
    "tle", // 1128
    "bo", // 1129
    "cc", // 1130
    "ble", // 1131
    "Look", // 1132
    " pushing", // 1133
    " founding", // 1134
    " holl", // 1135
    " hollow", // 1136
    "hell", // 1137
    "hello", // 1138
    " theft", // 1139
    " things", // 1140
    " man", // 1141
    " enter", // 1142
    " mech", // 1143
    " mechanis", // 1144
    " mechanism", // 1145
    "ger", // 1146
    "can", // 1147
    " vouch", // 1148
    " stay", // 1149
    " bolt", // 1150
    " kind", // 1151
    " road", // 1152
    " drop", // 1153
    " gravel", // 1154
    "show", // 1155
    " safe", // 1156
    "heck", // 1157
    "ching", // 1158
    "rel", // 1159
    "why", // 1160
    " Farmer", // 1161
    "about", // 1162
    "whose", // 1163
    " others", // 1164
    "confess", // 1165
    "goodbye", // 1166
    "thanks", // 1167
    " because", // 1168
    " days", // 1169
    " watching", // 1170
    "ss", // 1171
    " U", // 1172
    " tarp", // 1173
    " tarpaul", // 1174
    "cl", // 1175
    " His", // 1176
    " poisoned", // 1177
    " chains", // 1178
    " forced", // 1179
    " coins", // 1180
    " shut", // 1181
    " shutter", // 1182
    " ground", // 1183
    "eek", // 1184
    " hold", // 1185
    " P", // 1186
    " St", // 1187
    "act", // 1188
    "All", // 1189
    " deli", // 1190
    " pride", // 1191
    " look", // 1192
    "ach", // 1193
    " during", // 1194
    " could", // 1195
    " stru", // 1196
    " struck", // 1197
    " squ", // 1198
    " square", // 1199
};

#endif // NANOGPT_CONFIG_H
