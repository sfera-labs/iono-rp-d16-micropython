'''
Iono RP D16 library

    Copyright (C) 2022-2023 Sfera Labs S.r.l. - All rights reserved.

    For information, see:
    http://www.sferalabs.cc/

This code is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
See file LICENSE.txt for further informations on licensing terms.
'''

def DEBUG(msg):
    #print(msg)
    pass

def setBit(target, bitIdx, val):
    mask = 1 << bitIdx
    return (target & ~mask) | (mask if val else 0)

def getBit(source, bitIdx):
    return (source >> bitIdx) & 1
