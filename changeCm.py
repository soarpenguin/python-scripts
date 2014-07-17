import optparse
import sys
import getopt
import os
import json
#configure

def usage():
    print 'Usage:'
    print '    python changeCm.py --cm_conf=cm.conf --level_order="0:level_1,1:level_0" '
    print 'Options:'
    print '    -h,--help'
    print '        print help message.'
    print '    -v, --version'
    print '        print script version.'
    print '    -c cm.conf, --cm_conf=<cm.conf>'
    print '        configure file of cm.conf.'
    print '    -l <level_order_str>, --level_order=<level_order_str>'
    print '        level_order string to change the configure file of cm.conf'
    print 'Examples:'
    print '    python changeCm.py --cm_conf=cm.conf --level_order="0:level_1,1:level_0"'

def version():
    print 'changeCm.py 1.0.0.0'
    usage()

##############################################################
if __name__ == '__main__':
    RET_OK           = 0
    RET_FAILED       = 1
    RET_INVALID_ARGS = 2
    cm_conf = ''
    level_order = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvc:l:', ['help', 'version', 'cm_conf=', 'level_order='])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(RET_INVALID_ARGS)
    for opt, value in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(RET_FAILED)
        elif opt in ('-v', '--version'):
            version()
            sys.exit(RET_FAILED)
        elif opt in ('-c', '--cm_conf'):
            cm_conf = value
        elif opt in ('-l', '--level_order',):
            level_order = value
        else:
            print 'unknown option:' . opt
            sys.exit(RET_INVALID_ARGS)

    if str(cm_conf).strip() == '' or str(level_order).strip() == '':
        usage()
        sys.exit(RET_FAILED)

    if not os.path.exists(cm_conf):
        print "Please check the exists of the file:" + cm_conf
        sys.exit(RET_FAILED)

    try:
        f = file(cm_conf);
        jstr = json.load(f, encoding="GB2312")
        old_level = jstr["level_order"]
        array = str(level_order).split(',')

        level = {}
        for item in array:
            key, value = item.split(':')
            if key not in old_level.keys() or value not in old_level.values():
                print "bad key and value in level_order parameters."
                sys.exit(RET_FAILED)
            level[key] = value

        jstr["level_order"] = level
        print json.dumps(jstr, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False, encoding='utf-8').encode("gb2312")
        #print json.dumps(jstr, sort_keys=True, indent=4, separators=(',', ': '), encoding='utf-8')
    except Exception as e:
        print sys.exc_info()
        sys.exit(1)
