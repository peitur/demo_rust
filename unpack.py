#!/usr/bin/python3

import os, re, sys
import pathlib


import subprocess, shlex
from pprint import pprint


DEFAULT_SOURCE="trailer"
DEFAULT_TARGET="vendor"
CARGO_FILE="Cargo.toml"

class GenericCommand( object ):
    
    def __init__( self, cmd, **opt ):
        self.__debug = opt.get("debug", False )
        self.__data = list()        
        self.__cmd  = cmd
        self.__opt = opt
        
        if type( cmd ).__name__ in ( "str" ):
            self.__cmd  = shlex.split( cmd )
        else:
            self.__cmd  = [ str( s ) for s in  cmd ]

    def run_iterator( self ):

        if self.__debug: print( "CMD Running:> '%s'" % ( " ".join( self.__cmd ) ) )
        if self.__just_print:
             return ( 0, list() )
         
        prc = subprocess.Popen( self.__cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, cwd=self.__opt.get( "cwd", None ), universal_newlines=True, shell=False )
        for line in prc.stdout.readlines():
            yield line.rstrip()
            
            if prc.poll():
                break
            
        return ( prc.returncode, list() )
        

    def run_list( self ):

        res = list()
        
        if self.__debug: print( "CMD Running:> '%s'" % ( " ".join( self.__cmd ) ) )

        prc = subprocess.Popen( self.__cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, cwd=self.__opt.get( "cwd", None ), universal_newlines=True, shell=False )
        for line in prc.stdout.readlines():
            res.append( line.rstrip() )
            
            if prc.poll():
                break
            
        return ( prc.returncode, res )


def cargo_meta( dir, filename=CARGO_FILE ):
    values = dict()
    cfile = "%s/%s" % ( dir, filename )
    with open( cfile, "r" ) as fd:
        ctag = ""            

        for line in fd.readlines():
            line = line.rstrip().lstrip()

            if re.match( r"^\s*#.*" , line ) or len( line ) == 0:
                continue

            c_rx = re.match( r"\[\s*(\S+)\s*\]", line )
            if c_rx:
                ctag = c_rx.group(1)
            
            l_rx = re.match( r"^\s*(\S+)\s*=\s*\"(.+)\"", line )
            if l_rx:
                values[ "%s.%s" % ( ctag, l_rx.group(1)) ] = l_rx.group(2)
                
    return values


def get_crates( dir ):
    return [ f for f in pathlib.Path( dir ).iterdir() if re.match( ".+\.crate$", f.name ) ]

if __name__ == "__main__":
    pass    

    