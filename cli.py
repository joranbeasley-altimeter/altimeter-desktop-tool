import click

from altimeter_desktop_tool.api import iter_connect_raspberry_pi_in_ip_range
from altimeter_desktop_tool.ips import get_my_ip_range
def get_user_target_pi(yes=False):
    click.echo("Searching For Raspberry PI")
    my_range = get_my_ip_range()
    for cli in iter_connect_raspberry_pi_in_ip_range(*my_range):
        # print(cli._families_and_addresses())
        if not yes:
            with cli.lighted_context():
                if click.confirm("Do you see a solid green light above the sd card?"):
                    click.echo("\nFound PI! %s"%(cli._transport.sock.getpeername(),))
                    return cli
        else:
            return cli
        # cli.exec_command("sudo pkill -9 -f led0/brightness")
def print_pi_ips():
    click.echo("Searching For Raspberry PI")
    for cli in iter_connect_raspberry_pi_in_ip_range('192.168.0.1', '192.168.1.255'):
        print("  "+cli.getpeername()[0])
        cli.close()

@click.group()
@click.pass_context
def cli(ctx):
    pass

@cli.command()
def list():
    """
    List all the pi's that can be found on your network.
    """
    print_pi_ips()
if __name__ == "__main__":
    print_pi_ips()
