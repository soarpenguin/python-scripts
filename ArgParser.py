import argparse

def parse_argument():

    parser = argparse.ArgumentParser()

    parser.add_argument('-s', action = 'store',
                dest = 'simple_value',
                help = 'Store a simple value'
            )

    parser.add_argument('-c', action = 'store_const',
                dest = 'constant_value',
                const = 'value-to-store',
                help = 'Store a constant value'
            )

    parser.add_argument('-t', action = 'store_true',
                default = False,
                dest = 'boolean_switch',
                help = 'Set a switch to true'
            )

    parser.add_argument('-f', action = 'store_false',
                default = False,
                dest = 'boolean_switch',
                help = 'Set a switch to false'
            )

    parser.add_argument('-a', action = 'append',
                dest = 'collection',
                default = [],
                help = 'Set a switch to false'
            )

    parser.add_argument('--version', action = 'version',
                version = '%(prog)s 1.0'
            )

    results = parser.parse_args()

    return results

if __name__ == '__main__':

    results = parse_argument()

    print results.simple_value
    print results.constant_value
    print results.boolean_switch
    print results.boolean_switch
    print results.collection
    #print results.collection

