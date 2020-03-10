# Uploads a pilot.tar and a pilot.json to http://diracproject.web.cern.ch/diracproject/tars/Pilot/DIRAC/[directory]

# temp work dir
tmpdir=$(mktemp -d)
echo $tmpdir
cp Pilot/*.py $tmpdir
cp tests/pilot.json $tmpdir

# create the tar
cd $tmpdir
tar -cf pilot.tar *.py

# make the checksums file
sha512sum pilot.tar pilot.json *.py > checksums.sha512

# upload all the files
( tar -cf - pilot.tar pilot.json checksums.sha512 ) | ssh uploaduser@lxplus.cern.ch "cd /eos/project/d/diracgrid/www/tars/Pilot/DIRAC/${1}/ && tar -xvf - "
